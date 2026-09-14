import json
import os
import sys
import glob


def _as_int(s):
    """int(s) or None -- never raises, so a non-numeric enum literal (a plain
    name like "soft_light") is simply 'not an int', not an error."""
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def _parse_param(p: dict) -> dict:
    out = {
        "name": p.get("name"),
        "type": p.get("type"),
        "default": p.get("default"),
        "desc": p.get("shortdesc") or p.get("longdesc") or "",
    }
    if p.get("type") == "enum":
        entries = p.get("values", [])
        values = [v.get("name") for v in entries]
        out["values"] = values
        out["min"] = 0
        out["max"] = max(len(values) - 1, 0)
        # Enum params are stored as the ORDINAL INDEX into `values`, but some
        # nodes' .mmg entries carry a numeric `value` literal that does NOT
        # equal its index (e.g. wavelet_noise.type: "Mult 3" is index 4 but
        # its literal is "-3"). An author who types that literal instead of
        # the index gets a silent wrong render (it clamps to 0). Capture the
        # raw literals ONLY when at least one is a numeric string that differs
        # from its index, so the validator can name the intended index; enums
        # whose literals are plain names (blend, fbm) can't be confused with an
        # index and stay lean (no value_literals field).
        literals = [v.get("value") for v in entries]
        if any(_as_int(lit) is not None and _as_int(lit) != i
               for i, lit in enumerate(literals)):
            out["value_literals"] = literals
    else:
        for k in ("min", "max", "step"):
            if k in p:
                out[k] = p[k]
    return out


def _parse_generic_node(data: dict, type_name: str,
                         full_catalog: dict | None = None) -> dict | None:
    """Parse a compound/"generic" node: no shader_model, but a nested graph
    whose external interface is defined by its 'gen_inputs'/'gen_outputs'
    ios children (each exposing a 'ports' list) and whose external
    parameters come from a 'remote' node's widgets.

    `full_catalog` is the complete, already-built catalog (type_name ->
    parsed_node), used by `_resolve_widget_range` to resolve a widget whose
    linked inner node is a plain type reference (no inline shader_model of
    its own) rather than an inline shader node. It is optional so this
    function still works standalone (e.g. from `parse_node` on a single
    file) -- in that case a link to a type-referenced inner node simply
    can't be resolved and its range stays unset, same as before this fix.
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
            param = {
                "name": pname, "type": None, "default": None,
                "desc": w.get("shortdesc") or w.get("longdesc") or "",
            }
            resolved = _resolve_widget_range(child_nodes, w, full_catalog)
            if resolved is not None:
                # Keep this compound param's own name/desc; take the rest
                # (type/default/min/max/step/values) from the resolved
                # inner shader param.
                for k, v in resolved.items():
                    if k not in ("name", "desc"):
                        param[k] = v
            parameters.append(param)
    return {"type": type_name, "inputs": inputs,
            "outputs": outputs, "parameters": parameters}


def _resolve_widget_range(child_nodes: list, widget: dict,
                           full_catalog: dict | None = None) -> dict | None:
    """A compound/"generic" node's `remote` widgets only carry `name`/`desc`;
    the real range (type/min/max/step/default) usually lives elsewhere and
    has to be tracked down. There are three shapes, tried in this order:

    1. The widget carries its own range directly (a `named_parameter`-style
       widget with `min`/`max`/`step`/`default` fields right on it, no
       `linked_widgets` at all). Build the param dict straight from the
       widget.
    2. The widget has `linked_widgets` pointing at an inner node that is
       itself an inline `shader`-type node (it carries its own embedded
       `shader_model`). Look up the matching shader parameter there and
       parse it the same way a leaf node's own parameters are parsed.
    3. The widget's linked inner node has no inline `shader_model` -- it is
       a plain type reference (e.g. `"type": "voronoi"` with no nested
       shader block of its own). Its real parameters live in the
       separately-parsed catalog entry for that type. When `full_catalog`
       is supplied, look the type up there and search its own already-
       resolved `parameters` list for a matching name.

    Returns None (graceful fallback, never raises) when none of the above
    resolves -- e.g. the widget has no range of its own and no usable
    `linked_widgets`, the inner node can't be found, or (without
    `full_catalog`) the inner node is a type reference that can't be looked
    up here. Callers should leave the range fields unset in that case.
    """
    if "min" in widget and "max" in widget:
        return {
            "type": "float",
            "min": widget.get("min"),
            "max": widget.get("max"),
            "step": widget.get("step"),
            "default": widget.get("default"),
        }

    linked_widgets = widget.get("linked_widgets") or []
    if not linked_widgets:
        return None
    linked = linked_widgets[0]
    inner_name = linked.get("node")
    inner_param_name = linked.get("widget")
    if not inner_name or not inner_param_name:
        return None
    inner_node = next((n for n in child_nodes if n.get("name") == inner_name), None)
    if inner_node is None:
        return None
    inner_sm = inner_node.get("shader_model")
    if inner_sm:
        for p in inner_sm.get("parameters", []):
            if p.get("name") == inner_param_name:
                return _parse_param(p)
        return None
    # No inline shader_model: the inner node is a plain type reference.
    # Its real parameters live in the full catalog entry for that type.
    if full_catalog is None:
        return None
    referenced = full_catalog.get(inner_node.get("type"))
    if referenced is None:
        return None
    for p in referenced.get("parameters", []):
        if p.get("name") == inner_param_name:
            return dict(p)
    return None


def parse_node(mmg_path: str) -> dict | None:
    with open(mmg_path, encoding="utf-8") as fh:
        data = json.load(fh)
    type_name = os.path.splitext(os.path.basename(mmg_path))[0]
    return _parse_node_data(data, type_name)


def _parse_node_data(data: dict, type_name: str,
                      full_catalog: dict | None = None) -> dict | None:
    """The actual parsing logic behind `parse_node`, split out so
    `build_catalog` can re-invoke it for a compound/generic node's second
    pass without re-reading and re-parsing the file's JSON. `full_catalog`
    is forwarded to `_parse_generic_node` (see its docstring); leaf nodes
    (those with an inline `shader_model`) never need it.
    """
    sm = data.get("shader_model")
    if not sm:
        if "nodes" in data:
            return _parse_generic_node(data, type_name, full_catalog)
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


_MAX_FIXPOINT_ROUNDS = 10


def build_catalog(nodes_dir: str) -> dict:
    """Build the full node catalog in two passes.

    Pass 1 parses every .mmg file, exactly as before this function grew a
    second pass: each file's JSON is loaded once and parsed via
    `_parse_node_data`, producing a complete type_name -> parsed_node
    catalog. A leaf node's parameters already have their real ranges
    resolved at this point (via `_parse_param`); a compound/"generic" node's
    parameters are resolved as far as `_resolve_widget_range` can get
    without seeing the rest of the catalog (its own widget range, or a link
    to an inline shader node).

    Pass 2 revisits every compound/generic node parsed in pass 1 (tracked
    by keeping its already-loaded raw data) and re-resolves its parameters
    now that the full catalog is available. This is what lets
    `_resolve_widget_range` follow a `linked_widgets` link to an inner node
    that is a plain type reference rather than an inline shader node (e.g.
    crystal's 'voronoi' inner node has no shader_model of its own; its real
    parameters live in the separately-parsed 'voronoi' catalog entry, which
    may not exist yet -- or may not even be parsed yet -- during pass 1).
    See `_resolve_generic_nodes_to_fixpoint` for why pass 2 has to repeat to
    a fixpoint rather than run once.
    """
    catalog = {}
    generic_raw_data = {}  # type_name -> raw .mmg JSON, for pass 2
    for path in glob.glob(os.path.join(nodes_dir, "*.mmg")):
        type_name = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            node = _parse_node_data(data, type_name)
        except (ValueError, KeyError) as e:
            print(f"WARNING: skipping {os.path.basename(path)}: {e}", file=sys.stderr)
            node = None
        if node:
            catalog[node["type"]] = node
            if not data.get("shader_model"):
                generic_raw_data[node["type"]] = data

    _resolve_generic_nodes_to_fixpoint(catalog, generic_raw_data)
    return catalog


def _resolve_generic_nodes_to_fixpoint(catalog: dict, generic_raw_data: dict) -> None:
    """Re-resolve every compound/generic node's parameters against the
    current state of `catalog`, in place, repeating full rounds until one
    round makes no further change (a fixpoint).

    A single round is not enough: a compound node's `linked_control` can
    point at ANOTHER compound node's parameter, not just a leaf node's. That
    referenced compound node might not have had ITS OWN re-resolution
    applied yet within the same round -- whether it has depends on
    `generic_raw_data`'s iteration order, which mirrors `glob.glob()`'s
    order, which the stdlib does not guarantee to be sorted or stable
    across platforms or filesystems. Concretely: `binary_smooth.smooth`
    links to `fast_blur.param1`, and `fast_blur.param1` itself only
    resolves once `fast_blur` has been reprocessed with the full catalog
    available (it links to the leaf-referenced `fast_blur_shader.sigma`).
    A single sweep gives a different answer for `binary_smooth.smooth`
    depending on whether `binary_smooth` or `fast_blur` happens to be
    visited first -- silently reintroducing the exact nondeterminism this
    two-pass design exists to remove.

    Looping to a fixpoint fixes this: each round can only ever add a range
    that some later round could also have derived (re-parsing is
    idempotent once its inputs stop changing), so repeating until nothing
    changes converges on the same fully-resolved catalog regardless of
    which node happens to be visited first, in how many rounds it takes.

    Bounded by `_MAX_FIXPOINT_ROUNDS` so a cyclic compound reference (which
    would never converge) cannot hang the build. If the cap is hit, this
    warns to stderr -- matching this file's existing malformed-file warning
    convention -- rather than silently returning a half-resolved catalog.
    """
    for _round_num in range(_MAX_FIXPOINT_ROUNDS):
        changed = False
        for type_name, data in generic_raw_data.items():
            reparsed = _parse_generic_node(data, type_name, full_catalog=catalog)
            if reparsed is not None and reparsed != catalog.get(type_name):
                catalog[type_name] = reparsed
                changed = True
        if not changed:
            return
    print(
        f"WARNING: compound-node parameter resolution did not converge after "
        f"{_MAX_FIXPOINT_ROUNDS} rounds; the catalog may contain unresolved "
        "or order-dependent ranges (check for a cyclic compound reference)",
        file=sys.stderr,
    )


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
