# API sync tools

These scripts keep threadlepy in step with the Threadle backend. They are
development tools only and are not part of the installed package (only `src/` is packaged).
The same snapshot format and mapping file are used in threadleR (`tools/` there).

| File | What it is | Maintained by |
|---|---|---|
| `threadle-api.json` | Snapshot of the backend's commands and parameters | generated |
| `threadle-mapping.yaml` | What the code cannot tell: commands left unwrapped on purpose, planned wrappers | by hand |
| `check_api.py` | Compares the Python wrappers with the snapshot | — |
| `update_threadle_api.py`, `parse_threadle_help.py` | Regenerate the snapshot from a running backend | — |
| `api-coverage.md` | Coverage table, last generated report | generated |

## When the backend changes

```bash
# 1. Regenerate the snapshot (uses `threadle` on PATH, or pass --threadle "dotnet path/to/threadle.dll")
python3 tools/update_threadle_api.py

# 2. See what changed in the backend
git diff tools/threadle-api.json

# 3. Check the Python wrappers against it, and refresh the coverage table
python3 tools/check_api.py --report tools/api-coverage.md
```

`check_api.py` needs only PyYAML, does not import threadlepy or start Threadle,
and exits with status 1 on errors, so it also runs in CI (`.github/workflows/api-check.yaml`).

## What is checked

The mapping between Python functions and backend commands is read from the code:
a wrapper's command is the first argument of `call("...", locals())` or
`raw_cmd("...", {...})`. With `locals()`, every argument and every local variable
assigned before the call is sent under its own name, minus `drop=(...)`, the
argument holding the `assign=` name, and keys removed with `args.pop("x")`.

- **Errors** (break calls): a wrapper sends a command the backend does not have,
  sends an argument the backend does not know, or never sends a required argument;
  `threadle-mapping.yaml` lists a command the backend does not have.
- **Warnings** (may mislead users): different defaults or allowed values (from
  `Literal[...]` annotations and `_check(...)` calls), an argument optional in the
  backend but required in Python, a backend command with no wrapper that is not
  listed in `threadle-mapping.yaml`.
- **Notes**: Python supplies a default for an argument the backend requires. Usually a
  deliberate convenience; worth stating in the docstring.
