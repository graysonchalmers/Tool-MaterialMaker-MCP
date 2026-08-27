# src/mm_mcp/live.py
import json
import socket
from dataclasses import dataclass

# Must match addons/mm_live/live_server.gd's LIVE_PORT -- no shared-constant
# mechanism exists across GDScript and Python, so keep both literals in sync
# by hand if this ever changes.
LIVE_HOST = "127.0.0.1"
LIVE_PORT = 8765


@dataclass
class LiveResult:
    ok: bool
    data: dict | None = None
    error: str | None = None


def _send_command(cmd: dict, host: str = LIVE_HOST, port: int = LIVE_PORT,
                   timeout: float = 5.0) -> LiveResult:
    """Open a fresh TCP connection, send one JSON line, read one JSON line
    back, close. One-shot per call, matching the addon's per-connection
    dispatch -- there is no persistent session state on either side."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
    except OSError as exc:
        return LiveResult(ok=False, error=f"could not reach live server at {host}:{port}: {exc}")

    try:
        with sock:
            sock.sendall((json.dumps(cmd) + "\n").encode("utf-8"))
            sock.settimeout(timeout)
            buf = b""
            try:
                while b"\n" not in buf:
                    chunk = sock.recv(4096)
                    if not chunk:
                        return LiveResult(ok=False,
                                           error="connection closed before a response line arrived")
                    buf += chunk
            except TimeoutError:
                return LiveResult(ok=False,
                                   error=f"timed out waiting for a response from {host}:{port}")
    except OSError as exc:
        return LiveResult(ok=False, error=f"live server connection failed: {exc}")

    line = buf.split(b"\n", 1)[0]
    try:
        data = json.loads(line.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        return LiveResult(ok=False, error=f"malformed response from live server: {exc}")
    if not isinstance(data, dict):
        return LiveResult(ok=False, error="live server response was not a JSON object")
    if not data.get("ok", False):
        return LiveResult(ok=False, error=data.get("error", "live server reported failure"))
    return LiveResult(ok=True, data=data)


def ping(host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult:
    return _send_command({"cmd": "ping"}, host, port, timeout)


def get_graph(host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult:
    return _send_command({"cmd": "get_graph"}, host, port, timeout)
