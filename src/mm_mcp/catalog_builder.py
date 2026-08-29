import json
import os
import sys
import glob


def _parse_param(p: dict) -> dict:
    out = {
        "name": p.get("name"),
        "type": p.get("type"),
        "default": p.get("default"),
        "desc": p.get("shortdesc") or p.get("longdesc") or "",
    }
    if p.get("type") == "enum":
        values = [v.get("name") for v in p.get("values", [])]
        out["values"] = values
        out["min"] = 0
        out["max"] = max(len(values) - 1, 0)
    else:
        for k in ("min", "max", "step"):
            if k in p:
                out[k] = p[k]
    return out


def _parse_generic_node(data: dict, type_name: str) -> dict | None:
    """Parse a compound/"generic" node: no shader_model, but a nested graph
    whose external interface is defined by its 'gen_inputs'/'gen_outputs'
    ios children (each exposing a 'ports' list) and whose external
    parameters come from a 'remote' node's widgets.
    """
    child_nodes = data.get("nodes", [])
    gen_inputs = next((n for n in child_nodes
                        if n.get("type") == "ios" and n.get("name") == "gen_inputs"), None)
    gen_outputs = next((n for n in child_nodes
                         if n.get("type") == "ios" and n.get("name") == "gen_outputs"), None)
    if gen_inputs is None or gen_outputs is None:
        return None
    inputs = [
        {"name": p.get("name"), "type": p.get("type"),
         "desc": p.get("shortdesc") or p.get("longdesc") or ""}
        for p in gen_inputs.get("ports", [])
    ]
    outputs = [{"type": p.get("type")} for p in gen_outputs.get("ports", [])]
    parameters = []
    for n in child_nodes:
        if n.get("type") != "remote":
            continue
        for w in n.get("widgets", []):
            pname = w.get("name")
            if pname is None:
                continue
            parameters.append({
                "name": pname, "type": None, "default": None,
                "desc": w.get("shortdesc") or w.get("longdesc") or "",
            })
    return {"type": type_name, "inputs": inputs,
            "outputs": outputs, "parameters": parameters}


def parse_node(mmg_path: str) -> dict | None:
    with open(mmg_path, encoding="utf-8") as fh:
        data = json.load(fh)
    type_name = os.path.splitext(os.path.basename(mmg_path))[0]
    sm = data.get("shader_model")
    if not sm:
        if "nodes" in data:
            return _parse_generic_node(data, type_name)
        return None
    # "Generic" nodes repeat their '#'-suffixed input sockets generic_size
    # times (e.g. mwf_mix's 'h#'/'c#'/'orm#'/'em#'/'nm#' each repeat
    # generic_size times); the default repeat count is declared on the
    # .mmg file itself and can be overridden per-instance in a .ptex.
    #
    # `or 1` (not `.get(..., 1)`) is deliberate: it also coerces an explicit
    # `generic_size: 0` to 1. A 0 here would build a node with zero '#'
    # inputs, which is a broken interface, not a valid one -- so treating a
    # falsy value as "use the default 1" is safer than passing 0 through.
    # No bundled .mmg declares 0; this is defensive, not load-bearing.
    generic_size = data.get("generic_size") or 1
    inputs = []
    for i in sm.get("inputs", []):
        entry = {"name": i.get("name"), "type": i.get("type"),
                 "desc": i.get("shortdesc") or i.get("longdesc") or ""}
        reps = generic_size if "#" in (i.get("name") or "") else 1
        inputs.extend(dict(entry) for _ in range(reps))
    outputs = [{"type": o.get("type")} for o in sm.get("outputs", [])]
    parameters = [_parse_param(p) for p in sm.get("parameters", [])]
    return {"type": type_name, "inputs": inputs,
            "outputs": outputs, "parameters": parameters}


SPECIAL_TYPES = {"graph", "comment", "remote", "shader",
                 "buffer", "image", "switch", "debug", "ios"}


def build_catalog(nodes_dir: str) -> dict:
    catalog = {}
    for path in glob.glob(os.path.join(nodes_dir, "*.mmg")):
        try:
            node = parse_node(path)
        except (ValueError, KeyError) as e:
            print(f"WARNING: skipping {os.path.basename(path)}: {e}", file=sys.stderr)
            node = None
        if node:
            catalog[node["type"]] = node
    return catalog


def write_catalog(nodes_dir: str, out_path: str) -> int:
    catalog = build_catalog(nodes_dir)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, indent=1)
    return len(catalog)


if __name__ == "__main__":
    from mm_mcp.config import load_config
    cfg = load_config()
    out = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "catalog", "catalog.json",
    )
    count = write_catalog(cfg.nodes_dir, out)
    print(f"Wrote {count} node types to {out}")
