# Changelog

## Unreleased

## 0.2.0 - 2026-10-18

### Breaking changes

- `shortest_paths()` now wraps Threadle 1.3's `shortestpaths`, which returns exact
  distances for given node pairs: `shortest_paths(network, node1ids, node2ids,
  layernames=None, returnpaths=False)`. Migrate calls expecting an
  attribute-category result network to `shortest_paths_attributes()`.
- `rwdistances()` is removed; Threadle no longer has the command. Use `rwfpt()`
  instead.

### Features, fixes, and tooling

- Added GitHub Actions package builds and PyPI Trusted Publishing on published
  GitHub Releases, with release-tag and package-version checks.
- Added installed-wheel compatibility checks on Linux, Windows, and macOS with
  Python 3.9, 3.12, and 3.14, covering bundled resources and example-file copying.
- Documented the one-time PyPI publisher setup and subsequent release steps in
  `docs/releasing.md`.
- The Threadle process is now read through background threads instead of `select()`,
  so threadlepy also works on Windows. The backend's stderr is drained continuously
  (so a chatty backend can no longer stall on a full pipe) and its last lines are shown
  when the process fails.
- `stop()` first asks Threadle to exit on its own and closes the process pipes;
  `start()`/`stop()` log through the `threadlepy` logger instead of printing.
- `start()` warns when the running Threadle version differs from the one this
  version of threadlepy was written for (`client.SUPPORTED_THREADLE_VERSION`).
- Wrappers send only their own parameters to Threadle, never other local variables,
  and name the parameter that holds the result's variable name explicitly
  (`call(..., assign_from="name")`) instead of matching it by value.
- After a command times out, its late response is now discarded instead of being
  returned as the result of the next command.
- Arguments that take several node ids or names (`nodes`, `layernames`, ...) also
  accept a single value, e.g. `set_attrs(net, "x", nodes=5, attrvalue=1)`.
- `export()`: `layername` is optional (it is only required for gexf), and `format` is
  checked against gexf, graphml and pajek.
- New wrappers for the remaining Threadle 1.3 commands, matching threadleR 0.6.0:
  centrality (`betweenness_centrality()`, `closeness_centrality()`,
  `harmonic_centrality()`, `eigenvector_centrality()`, `pagerank()`,
  `edge_betweenness_centrality()`), cohesion and communities (`clustering_coefficient()`,
  `transitivity()`, `coreness()`, `constraint()`, `effective_size()`,
  `community_detection()`, `small_world_coefficient()`, `assortativity()`,
  `degree_assortativity()`), census and distances (`dyad_census()`, `triadic_census()`,
  `diameter()`, `eccentricity()`), layer and structure operations (`duplicate()`,
  `rename()`, `binary_to_valued()`, `symmetric_to_directed()`, `rewire()`,
  `merge_layers()`, `merge_networks()`, `merge_nodesets()`, `import_network()`),
  attributes and tables (`convert_attr()`, `set_attrs()`, `import_node_attributes()`,
  `get_attrs_table()`, `get_layer_stats()`, `get_alter_details()`), and `about()` /
  `system_info()`. All have `th_*` aliases.
- Added `scripts/test_threadle_13_commands.py`, which runs every new wrapper against a
  live Threadle process.
- The tutorial uses the new `shortest_paths()` and `shortest_paths_attributes()`, no
  longer calls `rwdistances()`, has a short section on the new network analyses, and
  was re-executed against Threadle 1.3.0.

## 0.1.4

- Added the `return_histograms` option to `rwfpt()` / `th_rwfpt()` to match the current threadleR wrapper.

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
