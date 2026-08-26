"""Phase 2 smoke: load a bundled example through the MCP layer and render it."""
import sys
from mm_mcp import server


def main() -> int:
    ptex = server.load_example("bricks")
    problems = [p for p in server.validate(ptex) if p["severity"] == "error"]
    if problems:
        print("VALIDATION ERRORS:", problems[:5])
        return 1
    result = server.render_graph(ptex, size=256, basename="smoke_bricks")
    if not result["ok"]:
        print("RENDER FAILED:", result.get("error"))
        print(result.get("log_tail", ""))
        return 1
    print(f"SMOKE PASS: rendered {len(result['images'])} image(s):")
    for img in result["images"]:
        print("  ", img)
    return 0


if __name__ == "__main__":
    sys.exit(main())
