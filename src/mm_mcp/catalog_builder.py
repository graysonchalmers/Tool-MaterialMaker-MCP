import json
import os


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


def parse_node(mmg_path: str) -> dict | None:
    with open(mmg_path, encoding="utf-8") as fh:
        data = json.load(fh)
    sm = data.get("shader_model")
    if not sm:
        return None
    type_name = os.path.splitext(os.path.basename(mmg_path))[0]
    inputs = [
        {"name": i.get("name"), "type": i.get("type"),
         "desc": i.get("shortdesc") or i.get("longdesc") or ""}
        for i in sm.get("inputs", [])
    ]
    outputs = [{"type": o.get("type")} for o in sm.get("outputs", [])]
    parameters = [_parse_param(p) for p in sm.get("parameters", [])]
    return {"type": type_name, "inputs": inputs,
            "outputs": outputs, "parameters": parameters}
