# addons/mm_live/live_server.gd
extends Node

## mm_live: thin socket server exposing live-control commands to an external
## Python client. Registered as a Godot [autoload] entry by overlay.py so it
## starts automatically whenever the disposable overlay project runs.
##
## LIVE_PORT below MUST match mm_mcp.live.LIVE_PORT on the Python side --
## there is no shared-constant mechanism across GDScript/Python, so keep
## both literals in sync by hand if this ever changes.
##
## Mutating commands (add_node/connect_nodes/set_param/render) were added in
## Phase 5 build step 3. See docs/superpowers/plans/2026-08-27-phase5-mutating-commands.md
## for the source citations behind each handler's Godot API calls. clear_graph
## was added later, same session as Phase 5's hands-on verification.

const LIVE_PORT := 8765

var _server := TCPServer.new()
var _connections: Array = []  # each entry: {peer: StreamPeerTCP, buf: PackedByteArray}


func _ready() -> void:
	var err := _server.listen(LIVE_PORT, "127.0.0.1")
	if err != OK:
		push_error("mm_live: failed to listen on port %d (error %d)" % [LIVE_PORT, err])


func _process(_delta: float) -> void:
	while _server.is_connection_available():
		_connections.append({"peer": _server.take_connection(), "buf": PackedByteArray()})

	var i := _connections.size() - 1
	while i >= 0:
		var entry: Dictionary = _connections[i]
		var peer: StreamPeerTCP = entry["peer"]
		peer.poll()
		if peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			_connections.remove_at(i)
			i -= 1
			continue

		var avail := peer.get_available_bytes()
		if avail > 0:
			var chunk = peer.get_partial_data(avail)
			if chunk[0] == OK:
				entry["buf"].append_array(chunk[1])

		var newline_idx: int = entry["buf"].find(10)  # ASCII "\n"
		if newline_idx != -1:
			var line: String = entry["buf"].slice(0, newline_idx).get_string_from_utf8()
			_dispatch(peer, line)
			_connections.remove_at(i)

		i -= 1


func _dispatch(peer: StreamPeerTCP, line: String) -> void:
	var response: Dictionary
	var parsed = JSON.parse_string(line)
	if typeof(parsed) != TYPE_DICTIONARY or not parsed.has("cmd"):
		response = {"ok": false, "error": "malformed command"}
	else:
		match parsed["cmd"]:
			"ping":
				response = _cmd_ping()
			"get_graph":
				response = _cmd_get_graph()
			"add_node":
				response = await _cmd_add_node(parsed)
			"connect_nodes":
				response = _cmd_connect_nodes(parsed)
			"disconnect_nodes":
				response = _cmd_disconnect_nodes(parsed)
			"reposition_node":
				response = _cmd_reposition_node(parsed)
			"set_param":
				response = _cmd_set_param(parsed)
			"render":
				response = await _cmd_render(parsed)
			"clear_graph":
				response = await _cmd_clear_graph()
			_:
				response = {"ok": false, "error": "unknown command: %s" % str(parsed["cmd"])}
	peer.put_data((JSON.stringify(response) + "\n").to_utf8_buffer())


func _cmd_ping() -> Dictionary:
	# mm_globals.main_window is null until the main scene finishes loading --
	# resolved fresh on every call, never cached, so a probe issued right
	# after launch correctly reports "not ready yet" instead of a stale null.
	# main_window resolving does NOT mean a graph tab exists yet -- the two
	# happen in separate boot steps, so has_graph is reported as its own
	# field rather than folded into `ready`; connect_or_launch on the Python
	# side is what decides how to combine them (both are required there).
	return {"ok": true, "ready": mm_globals.main_window != null,
			"has_graph": _has_active_graph()}


func _has_active_graph() -> bool:
	if mm_globals.main_window == null:
		return false
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	return graph_edit != null and graph_edit.generator != null


func _cmd_get_graph() -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	return {"ok": true, "graph": graph_edit.generator.serialize()}


func _cmd_add_node(cmd: Dictionary) -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var node_type = cmd.get("type")
	if typeof(node_type) != TYPE_STRING or node_type.is_empty():
		return {"ok": false, "error": "add_node requires a non-empty 'type' string"}
	var position := Vector2(float(cmd.get("x", 0)), float(cmd.get("y", 0)))
	var data := {"type": node_type, "parameters": cmd.get("parameters", {})}
	var created: Array = await graph_edit.create_nodes(data, position)
	if created.is_empty():
		return {"ok": false, "error": "Material Maker rejected node type '%s'" % node_type}
	# create_nodes may rename the node on a collision (see gen_graph.gd's
	# add_generator -- it uniquifies the name), so the authoritative name is
	# read back off the created node's generator, never assumed to match
	# the caller's request (there usually isn't a requested name at all).
	return {"ok": true, "name": created[0].generator.name}


func _cmd_connect_nodes(cmd: Dictionary) -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var from_name := str(cmd.get("from"))
	var to_name := str(cmd.get("to"))
	var from_node_name := "node_" + from_name
	var to_node_name := "node_" + to_name
	if not graph_edit.has_node(from_node_name):
		return {"ok": false, "error": "no node named '%s' in the live graph" % from_name}
	if not graph_edit.has_node(to_node_name):
		return {"ok": false, "error": "no node named '%s' in the live graph" % to_name}
	var connected: bool = graph_edit.do_connect_node(
			from_node_name, int(cmd.get("from_port", 0)),
			to_node_name, int(cmd.get("to_port", 0)))
	if not connected:
		return {"ok": false, "error": "Material Maker refused the connection (incompatible ports?)"}
	return {"ok": true}


func _cmd_disconnect_nodes(cmd: Dictionary) -> Dictionary:
	# Mirrors _cmd_connect_nodes exactly, calling Material Maker's own
	# do_disconnect_node (graph_edit.gd) instead of do_connect_node -- the
	# missing counterpart that lets a caller fully restore a port to
	# "unconnected" rather than only ever reconnecting it to something else.
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var from_name := str(cmd.get("from"))
	var to_name := str(cmd.get("to"))
	var from_node_name := "node_" + from_name
	var to_node_name := "node_" + to_name
	if not graph_edit.has_node(from_node_name):
		return {"ok": false, "error": "no node named '%s' in the live graph" % from_name}
	if not graph_edit.has_node(to_node_name):
		return {"ok": false, "error": "no node named '%s' in the live graph" % to_name}
	var disconnected: bool = graph_edit.do_disconnect_node(
			from_node_name, int(cmd.get("from_port", 0)),
			to_node_name, int(cmd.get("to_port", 0)))
	if not disconnected:
		return {"ok": false, "error": "no such connection to remove"}
	return {"ok": true}


func _cmd_reposition_node(cmd: Dictionary) -> Dictionary:
	# Mirrors _cmd_connect_nodes/_cmd_disconnect_nodes's addressing, but reuses
	# do_set_position (minimal.gd) instead of a connection primitive -- the
	# exact same call graph_edit.gd's own undoredo_command "move_generators"
	# case makes when the parent generator is the currently-open graph. That
	# call's _on_offset_changed handler (minimal.gd) also writes the new
	# position back onto the generator itself (generator.set_position), so a
	# subsequent get_graph/serialize() reflects the move -- not just the
	# GraphNode's on-screen position.
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var node_name := str(cmd.get("name"))
	var node_path := "node_" + node_name
	if not graph_edit.has_node(node_path):
		return {"ok": false, "error": "no node named '%s' in the live graph" % node_name}
	var node = graph_edit.get_node(node_path)
	node.do_set_position(Vector2(float(cmd.get("x", 0)), float(cmd.get("y", 0))))
	return {"ok": true}


func _cmd_set_param(cmd: Dictionary) -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var node_name := str(cmd.get("name"))
	var node_path := NodePath(node_name)
	if not graph_edit.generator.has_node(node_path):
		return {"ok": false, "error": "no node named '%s' in the live graph" % node_name}
	var target = graph_edit.generator.get_node(node_path)
	graph_edit.set_node_parameters(target, cmd.get("parameters", {}))
	return {"ok": true}


func _cmd_render(cmd: Dictionary) -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var prefix := str(cmd.get("prefix", ""))
	var profile := str(cmd.get("profile", "Godot/Godot 4 Standard"))
	if prefix.is_empty():
		return {"ok": false, "error": "render requires a non-empty 'prefix'"}
	var material_node = graph_edit.get_material_node()
	if material_node == null:
		return {"ok": false, "error": "no material node in the active graph"}
	# Call the material node's own export_material directly (gen_material.gd:650)
	# rather than main_window.export_material, which forwards to
	# graph_edit.export_material WITHOUT awaiting it -- so awaiting THAT call
	# resolves same-frame while the real file-writing coroutine keeps running
	# in the background, unobserved (confirmed empirically). command_line=true
	# (gen_material.gd's 4th param) skips the interactive overwrite dialog,
	# which would otherwise await user input forever inside this socket-driven
	# command -- the same flag the proven --export-material CLI path uses.
	await material_node.export_material(prefix, profile, 0, true)
	return {"ok": true}


func _cmd_clear_graph() -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null:
		return {"ok": false, "error": "no active graph tab"}
	# graph_edit.gd:714's new_material() is the same reset the GUI's own
	# "New" menu item performs on the current tab -- it calls clear_material()
	# then rebuilds from its default init_nodes (a single "Material" node, no
	# connections), so this does not need to specify that shape itself. It is
	# a coroutine (awaits mm_loader.create_gen internally), so this must be
	# awaited directly -- the same await-or-it-resolves-same-frame bug class
	# that hit _cmd_render's export_material call applies here too.
	await graph_edit.new_material()
	_show_transient_notice("Claude cleared the graph")
	return {"ok": true}


func _show_transient_notice(text: String) -> void:
	# Non-blocking, non-modal: a person watching the window sees this happen,
	# but nothing waits on them dismissing it -- a remote clear must never
	# hang the socket response on a human being at the keyboard. Material
	# Maker has no existing toast/notification system to reuse (only blocking
	# AcceptDialogs), so this is a minimal self-contained overlay.
	var layer := CanvasLayer.new()
	layer.layer = 100
	var label := Label.new()
	label.text = text
	label.add_theme_color_override("font_color", Color.WHITE)
	label.add_theme_font_size_override("font_size", 18)
	label.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	label.position = Vector2(-320, 20)
	label.size = Vector2(300, 30)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	layer.add_child(label)
	get_tree().root.add_child(layer)
	var timer := get_tree().create_timer(3.0)
	timer.timeout.connect(layer.queue_free)
