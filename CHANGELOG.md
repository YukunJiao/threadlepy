# Changelog

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
