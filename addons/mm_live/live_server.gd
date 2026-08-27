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
## This step only implements "ping" and "get_graph". Mutating commands
## (add_node/connect_nodes/set_param/render) are Phase 5 build step 3.
## Deliberately no validation here -- everything mutating arrives
## pre-validated from the Python side (see the design spec).

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
