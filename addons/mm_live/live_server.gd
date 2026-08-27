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
## for the source citations behind each handler's Godot API calls.

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
			_:
				response = {"ok": false, "error": "unknown command: %s" % str(parsed["cmd"])}
	peer.put_data((JSON.stringify(response) + "\n").to_utf8_buffer())


func _cmd_ping() -> Dictionary:
	# mm_globals.main_window is null until the main scene finishes loading --
	# resolved fresh on every call, never cached, so a probe issued right
	# after launch correctly reports "not ready yet" instead of a stale null.
	return {"ok": true, "ready": mm_globals.main_window != null}


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
