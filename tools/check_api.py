"""Compare threadlepy's wrapper functions with the Threadle backend API.

Reads tools/threadle-api.json (see tools/update_threadle_api.py) and
tools/threadle-mapping.yaml, statically inspects every function in
src/threadlepy/ that sends a fixed backend command, and reports:
  errors   - things that break calls: unknown commands, arguments the backend
             does not know, required backend arguments never sent
  warnings - things that may mislead users: different defaults or choices,
             backend commands with no wrapper and no entry in the mapping file
  notes    - Python supplies a default for an argument the backend requires

The package is not imported, so no Threadle process is needed.

Usage (from the repository root):
    python3 tools/check_api.py                  # print report, exit 1 on errors
    python3 tools/check_api.py --report FILE    # also write a Markdown report
"""
import argparse
import ast
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "threadlepy"
TOOLS = ROOT / "tools"

# ---- Backend -----------------------------------------------------------------


def backend_params(cmd):
    out = {}
    for p in cmd["params"]:
        alts = p.get("one_of", [p])
        for a in alts:
            if a.get("name"):
                out[a["name"]] = dict(a, required=a.get("required", False) and "one_of" not in p)
    return out


# ---- Python wrappers ---------------------------------------------------------

_MISSING = object()


def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return _MISSING


def module_choices(tree):
    """Module-level Literal[...] aliases and tuple constants, by name."""
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if value is None:
                continue
            vals = None
            if isinstance(value, ast.Subscript) and getattr(value.value, "id", None) == "Literal":
                vals = literal(value.slice)
                vals = vals if isinstance(vals, tuple) else (vals,)
            elif isinstance(value, ast.Tuple):
                vals = literal(value)
            if vals is not None and vals is not _MISSING:
                for t in targets:
                    if isinstance(t, ast.Name):
                        out[t.id] = [str(v) for v in vals]
    return out


def annotation_choices(ann, choices):
    """Choices from an annotation like Direction or Optional[Direction]."""
    if isinstance(ann, ast.Name):
        return choices.get(ann.id)
    if isinstance(ann, ast.Subscript):
        if getattr(ann.value, "id", None) == "Literal":
            vals = literal(ann.slice)
            if vals is not _MISSING:
                return [str(v) for v in (vals if isinstance(vals, tuple) else (vals,))]
        if getattr(ann.value, "id", None) == "Optional":
            return annotation_choices(ann.slice, choices)
    return None



def dict_key_edits(func, var, after_line, before_line):
    """Keys added (`var["k"] = ...`) and removed (`var.pop("k")`, `del var["k"]`)."""
    added, removed = set(), set()
    for sub in ast.walk(func):
        line = getattr(sub, "lineno", 0)
        if not after_line <= line < before_line:
            continue
        if isinstance(sub, ast.Assign):
            for t in sub.targets:
                if isinstance(t, ast.Subscript) and getattr(t.value, "id", None) == var:
                    key = literal(t.slice)
                    if isinstance(key, str):
                        added.add(key)
        elif isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "pop" \
                and getattr(sub.func.value, "id", None) == var and sub.args:
            key = literal(sub.args[0])
            if isinstance(key, str):
                removed.add(key)
        elif isinstance(sub, ast.Delete):
            for t in sub.targets:
                if isinstance(t, ast.Subscript) and getattr(t.value, "id", None) == var:
                    key = literal(t.slice)
                    if isinstance(key, str):
                        removed.add(key)
    return added, removed


def is_locals_call(node):
    """locals() or locals().copy() / dict(locals())."""
    if isinstance(node, ast.Call):
        if getattr(node.func, "id", None) == "locals":
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == "copy":
            return is_locals_call(node.func.value)
        if getattr(node.func, "id", None) == "dict" and node.args:
            return is_locals_call(node.args[0])
    return False


def inspect_function(func, path, choices):
    params = func.args.posonlyargs + func.args.args + func.args.kwonlyargs
    defaults = [None] * (len(func.args.posonlyargs + func.args.args) - len(func.args.defaults)) \
        + list(func.args.defaults) + list(func.args.kw_defaults)
    formals = {}
    for p, d in zip(params, defaults):
        formals[p.arg] = {
            "has_default": d is not None,
            "default": literal(d) if d is not None else _MISSING,
            "choices": annotation_choices(p.annotation, choices),
        }
    for sub in ast.walk(func):  # _check(x, CONSTANTS, "x")
        if isinstance(sub, ast.Call) and getattr(sub.func, "id", None) == "_check" and len(sub.args) >= 2:
            name, allowed = getattr(sub.args[0], "id", None), getattr(sub.args[1], "id", None)
            if name in formals and allowed in choices:
                formals[name]["choices"] = choices[allowed]

    for sub in ast.walk(func):
        if not (isinstance(sub, ast.Call) and getattr(sub.func, "id", None) in ("call", "raw_cmd") and sub.args):
            continue
        cmd = literal(sub.args[0])
        if not isinstance(cmd, str):
            continue
        kw = {k.arg: k.value for k in sub.keywords}
        payload = sub.args[1] if len(sub.args) > 1 else kw.get("locals_dict", kw.get("args"))

        if sub.func.id == "raw_cmd":
            sent = {literal(k) for k in payload.keys} if isinstance(payload, ast.Dict) else set()
        elif payload is not None and is_locals_call(payload):
            # call() sends only the wrapper's own parameters, never other locals
            sent = set(formals)
        elif isinstance(payload, ast.Name):
            # args = locals().copy(); args["x"] = ...; call("cmd", args)
            origin = next((a for a in ast.walk(func) if isinstance(a, ast.Assign)
                           and any(getattr(t, "id", None) == payload.id for t in a.targets)
                           and is_locals_call(a.value)), None)
            if origin is None:
                continue
            sent = set(formals)
            added, removed = dict_key_edits(func, payload.id, origin.lineno, sub.lineno)
            sent = (sent | added) - removed
        else:
            continue

        drop = literal(kw["drop"]) if "drop" in kw else ()
        sent -= set(drop if isinstance(drop, tuple) else (drop,))
        sent -= {"cmd", "assign"}
        if isinstance(kw.get("assign_from"), ast.Constant):  # parameter holding the assign name
            sent.discard(kw["assign_from"].value)
        if isinstance(kw.get("assign"), ast.Name):  # older convention: assign=<parameter>
            sent.discard(kw["assign"].id)
        if isinstance(kw.get("extra"), ast.Dict):  # arguments sent besides the parameters
            sent |= {literal(k) for k in kw["extra"].keys if isinstance(literal(k), str)}

        return {
            "name": func.name,
            "cmd": cmd,
            "file": str(path.relative_to(ROOT)),
            "line": func.lineno,
            "formals": formals,
            "sent": sent,
        }
    return None


def find_wrappers():
    wrappers = []
    for path in sorted(SRC.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        choices = module_choices(tree)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                w = inspect_function(node, path, choices)
                if w:
                    wrappers.append(w)
    return wrappers


# ---- Compare -----------------------------------------------------------------


def same_value(py, be):
    if py is None or be is None:  # None in Python = not sent, the backend decides
        return True
    pv = str(py).lower()
    bv = str(be).lower().replace("\\t", "\t").replace("\\n", "\n")
    try:
        return float(pv) == float(bv)
    except ValueError:
        return pv == bv


def check(api, mapping, wrappers):
    backend = {c["name"]: c for c in api["commands"]}
    errors, warnings, notes = [], [], []
    ignored = mapping.get("py_only_args") or {}

    for w in wrappers:
        where = f"{w['name']} ({w['file']}:{w['line']})"
        b = backend.get(w["cmd"])
        if b is None:
            errors.append(f"{where}: sends command '{w['cmd']}', which the backend does not have")
            continue
        bp = backend_params(b)
        skip = set(ignored.get("*", [])) | set(ignored.get(w["name"], []))

        for a in sorted(w["sent"] - skip):
            if a not in bp:
                errors.append(f"{where}: argument '{a}' is not a parameter of backend '{w['cmd']}'")
        for p in bp.values():
            if p["required"] and p["name"] not in w["sent"]:
                errors.append(f"{where}: backend '{w['cmd']}' requires '{p['name']}', which the function never sends")
        for a in sorted(w["sent"] & set(bp)):
            p, f = bp[a], w["formals"].get(a)
            if f is None:  # set inside the function body, not a Python argument
                continue
            if p["required"] and f["has_default"] and f["default"] is not None:
                notes.append(f"{w['name']}: '{a}' is required by the backend; Python supplies the default {f['default']!r}")
            if not p["required"] and not f["has_default"]:
                warnings.append(f"{where}: '{a}' is optional in the backend but required in Python")
            if f["has_default"] and f["default"] is not _MISSING and "default" in p \
                    and not same_value(f["default"], p["default"]):
                warnings.append(f"{where}: default of '{a}' is {f['default']!r} in Python "
                                f"but {p['default']!r} in the backend")
            if f["choices"] and p.get("choices"):
                py_c = {str(c).lower() for c in f["choices"]}
                be_c = {str(c).lower() for c in p["choices"]}
                if py_c != be_c:
                    warnings.append(f"{where}: choices for '{a}' are {{{', '.join(sorted(py_c))}}} in Python "
                                    f"but {{{', '.join(sorted(be_c))}}} in the backend")

    wrapped = {w["cmd"] for w in wrappers}
    not_wrapped = set(mapping.get("not_wrapped") or {})
    planned = set(mapping.get("planned") or {})
    for c in sorted(set(backend) - wrapped - not_wrapped - planned):
        warnings.append(f"backend command '{c}' has no Python wrapper and is not listed in threadle-mapping.yaml")
    for c in sorted((not_wrapped | planned) & wrapped):
        warnings.append(f"'{c}' is listed in threadle-mapping.yaml but now has a Python wrapper")
    for c in sorted((not_wrapped | planned) - set(backend)):
        errors.append(f"threadle-mapping.yaml lists '{c}', which the backend does not have")
    return backend, errors, warnings, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", help="write a Markdown coverage report to this file")
    opts = ap.parse_args()

    api = json.loads((TOOLS / "threadle-api.json").read_text(encoding="utf-8"))
    mapping = yaml.safe_load((TOOLS / "threadle-mapping.yaml").read_text(encoding="utf-8")) or {}
    wrappers = find_wrappers()
    backend, errors, warnings, notes = check(api, mapping, wrappers)

    # The client warns at startup when the backend differs from SUPPORTED_THREADLE_VERSION;
    # keep that in step with the snapshot the wrappers are checked against.
    client_tree = ast.parse((SRC / "client.py").read_text(encoding="utf-8"))
    supported = next((literal(n.value) for n in client_tree.body if isinstance(n, ast.Assign)
                      and any(getattr(t, "id", None) == "SUPPORTED_THREADLE_VERSION" for t in n.targets)), None)
    snapshot = ".".join(str(api["threadle_version"]).split(".")[:2])
    if supported != snapshot:
        errors.append(f"client.py: SUPPORTED_THREADLE_VERSION is {supported!r}, "
                      f"but tools/threadle-api.json is for Threadle {snapshot}")

    wrapped = {w["cmd"] for w in wrappers}
    not_wrapped = mapping.get("not_wrapped") or {}
    planned = mapping.get("planned") or {}
    unmapped = set(backend) - wrapped - set(not_wrapped) - set(planned)
    summary = [
        f"Threadle backend {api['threadle_version']}: {len(backend)} commands",
        f"  wrapped in Python:   {len(wrapped & set(backend))} (by {len(wrappers)} functions)",
        f"  not wrapped (by design): {len(not_wrapped)}",
        f"  planned:             {len(planned)}",
        f"  unmapped:            {len(unmapped)}",
        f"Errors: {len(errors)}, warnings: {len(warnings)}, notes: {len(notes)}",
    ]
    print("\n".join(summary))
    for title, items in (("ERRORS", errors), ("WARNINGS", warnings), ("NOTES", notes)):
        if items:
            print(f"\n{title}")
            print("\n".join(f"  - {x}" for x in items))

    if opts.report:
        def status(cmd):
            fns = [w["name"] for w in wrappers if w["cmd"] == cmd]
            if fns:
                return ", ".join(f"`{f}()`" for f in fns)
            if cmd in not_wrapped:
                return f"not wrapped: {not_wrapped[cmd]}"
            if cmd in planned:
                return f"planned: {planned[cmd]}"
            return "**unmapped**"
        md = ["# threadlepy API coverage", "",
              f"Generated by `tools/check_api.py` against Threadle {api['threadle_version']}.", "",
              *(f"    {s}" for s in summary), "",
              "| Backend command | Python |", "|---|---|",
              *(f"| `{c}` | {status(c)} |" for c in sorted(backend))]
        for title, items in (("Errors", errors), ("Warnings", warnings), ("Notes", notes)):
            if items:
                md += ["", f"## {title}", "", *(f"- {x}" for x in items)]
        Path(opts.report).write_text("\n".join(md) + "\n", encoding="utf-8")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
