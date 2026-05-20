# Changelog

## 0.1.3

- Aligned `load_examples()` with threadleR behavior by assigning example handles by default and restoring the previous Threadle working directory after loading.
- Added regression coverage for `load_examples()` workdir restoration and assignment behavior.
- Added `scripts/test_all_commands_example_data.py`, an end-to-end workflow modeled after the threadleR example-data command script.
- Ignored generated `threadle_examples/` and `threadle_outputs/` directories.

## 0.1.2

- Added one-line docstrings for public command wrappers.
- Added `Literal` type hints for finite-choice parameters to improve editor completions.
- Marked the package as typed with `py.typed`.

## 0.1.1

- Updated PyPI project description to match README.
- Synchronized package metadata version with the 0.1.1 release.

## 0.1.0

- Expanded Python command wrappers to better correspond to Threadle.
- Added `th_*` aliases for users moving between threadleR and threadlepy.
- Added bundled example-data workflow through `load_examples()`.
- Added `scripts/test_commands.py` integration smoke test.
- Added `scripts/test_session.py` smoke test for context-managed sessions.
- Added `docs/threadlepy_tutorial.ipynb` tutorial notebook.
- Added `threadlepy.session()` for context-managed Threadle process lifecycle.
- Improved Threadle executable checks and process-exit error reporting.
- Improved API compatibility for `layername` / `layernames`, `th_cmd(cmd=...)`, `addmissingaffiliation`, and related legacy arguments.
- Added package-data configuration for example TSV and script files.
- Cleaned generated artifacts from the repository and updated `.gitignore`.

threadlepy follows its own PyPI versioning. Its API is designed to correspond
to Threadle CLI commands and is inspired by threadleR, but version numbers are
not synchronized with threadleR releases.
