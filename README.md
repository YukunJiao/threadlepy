# threadlepy

`threadlepy` is a Python client for the **Threadle CLI** JSON interface.
It starts a Threadle subprocess, sends commands over stdin/stdout, and exposes
Python wrappers that mirror the core workflow of
[`YukunJiao/threadleR`](https://github.com/YukunJiao/threadleR).

> Status: experimental. The wrapper names and returned payload shapes follow the
> Threadle CLI and may evolve with the backend.

`threadlepy` follows its own PyPI versioning. Its API is designed to correspond
to Threadle CLI commands and is inspired by `threadleR`, but version numbers are
not synchronized with `threadleR` releases.

## Installation

```bash
pip install threadlepy
```

For local development:

```bash
pip install -e .
```

Requirements:

- Python 3.9+
- A working Threadle CLI executable named `threadle` on `PATH`, or a full path
  passed to `threadlepy.start()`

## Quick Start

```python
import threadlepy
import threadlepy.commands as th

threadlepy.configure(timeout=3600)
threadlepy.start()

examples = th.load_examples("lazega")
lazega = examples["lazega"]

th.info(lazega)
th.get_node_alters(lazega, nodeid=23, layernames="friends", direction="out")
th.shortest_path(lazega, node1id=1, node2id=23, layernames="friends")

threadlepy.stop()
```

You can also manage the Threadle process with a context manager:

```python
import threadlepy
import threadlepy.commands as th

with threadlepy.session(timeout=3600):
    examples = th.load_examples("mynet")
    print(th.info(examples["mynet"]))
```

If `threadle` is not on `PATH`, pass the full executable path to
`threadlepy.start("/full/path/to/threadle")` or
`threadlepy.session("/full/path/to/threadle")`.

## Integration Test Script

The repository includes a threadleR-style smoke test that exercises the public
command wrappers against bundled example data:

```bash
python scripts/test_commands.py
```

If `threadle` is not on `PATH`, pass the executable explicitly:

```bash
python scripts/test_commands.py --threadle /full/path/to/threadle
```

There is also a small lifecycle smoke test for the recommended scripting style
with `threadlepy.session()`:

```bash
python scripts/test_session.py
```

or:

```bash
python scripts/test_session.py --threadle /full/path/to/threadle
```

The script:

- starts and stops the Threadle CLI process
- loads `mynet` from the bundled example data
- runs inventory, metadata, node, attribute, edge, path, degree, density,
  component, two-mode, transformation, import/export, raw-command, and cleanup
  commands
- creates a scratch network for mutating commands so the example workflow stays
  easy to inspect

When the Threadle executable is unavailable, the script exits with code `77`
and prints a skip message.

## Tutorial Notebook

A runnable tutorial notebook is available at:

```text
docs/threadlepy_tutorial.ipynb
```

Open it with Jupyter, VS Code, or another notebook UI:

```bash
jupyter notebook docs/threadlepy_tutorial.ipynb
```

The notebook follows the same design as the threadleR vignette: start Threadle,
load example data, inspect nodes and attributes, work with one-mode and two-mode
layers, derive structures, edit a scratch network, import/export files, and
clean up.

## Handles

Commands that create or load structures return lightweight Python handles:

```python
ns = th.create_nodeset("ns", createnodes=5)
net = th.create_network("net", ns)
```

A handle stores the backend variable name. Any wrapper that expects a network or
nodeset also accepts the raw backend name as a string.

Most wrappers are available in two styles: Pythonic names such as
`create_nodeset()` and `shortest_path()`, plus `threadleR`-style aliases such as
`th_create_nodeset()` and `th_shortest_path()`.

## Working Directory and Examples

```python
th.get_workdir()
th.set_workdir("~/my_threadle_workspace")
th.sync_wd()

example_dir = th.stage_examples_to_wd("threadle_examples")
th.set_workdir(example_dir)
```

Bundled datasets can be loaded directly:

```python
objs = th.load_examples(["mynet", "lazega"])
mynet = objs["mynet"]
```

## Creating and Editing Networks

```python
ns = th.create_nodeset("people", createnodes=10)
net = th.create_network("relations", ns)

th.add_layer(net, "friends", mode=1, directed=False, valuetype="binary")
th.add_edge(net, "friends", 1, 2)
th.check_edge(net, "friends", 1, 2)
th.remove_edge(net, "friends", 1, 2)

th.add_layer(net, "clubs", mode=2)
th.add_hyper(net, "clubs", "club_a", nodes=[1, 2, 3])
th.add_aff(net, "clubs", nodeid=4, hypername="club_a")
th.get_hyperedge_nodes(net, "clubs", "club_a")
```

## Attributes

```python
th.define_attr(ns, "group", "string")
th.set_attr(ns, nodeid=1, attrname="group", attrvalue="A")
th.get_attr(ns, nodeid=1, attrname="group")

th.generate_attr(ns, "score", attrtype="int", min=1, max=10)
th.get_attr_summary(ns, "score")
th.get_attrs(ns, nodes=[1, 2, 3], attrname="score")
```

## Queries and Measures

```python
th.get_all_nodes(ns, offset=0, limit=100)
th.get_all_edges(net, "friends", offset=0, limit=1000)
th.get_degree(net, nodeid=1, layernames="friends", direction="both")
th.degree(net, "friends", attrname="friends_degree", direction="both")
th.density(net, "friends", samplesize=500)
th.components(net, "friends", attrname="component")
```

Multiple layer names can be passed as a Python list; the client sends the
semicolon-separated format expected by Threadle:

```python
th.shortest_path(net, 1, 8, layernames=["friends", "coworkers"])
```

## Transformations and Random Walks

```python
th.symmetrize(net, "advice", method="max", newlayername="advice_sym")
th.project_two_mode(net, "clubs", method="count", newlayername="club_projection")
th.pack(net, "friends")
th.unpack(net, "friends")

rw = th.rwdistances("rw_dist", net, attrname="group", maxsteps=100)
mfpt = th.rwfpt("mfpt", net, attrname="group", maxsteps=100, minpairobs=10)
```

## File IO

```python
th.save_file(ns, "people.tsv")
ns2 = th.load_file("people2", "people.tsv", type="nodeset")

th.export_layer(net, "friends", "friends.tsv", header=True, sep="\t")
th.import_layer(net, "friends", "friends.tsv", format="edgelist", header=True)
th.export(net, format="gexf", file="friends.gexf", layername="friends")
```

## Raw Commands

Use `threadlepy.raw_cmd()` or `th.cmd()` for backend commands that do not yet
have a typed wrapper:

```python
payload = threadlepy.raw_cmd("i")
handle = th.cmd("createnodeset", {"createnodes": 3}, assign="tmp", type="nodeset")
```

## Function Coverage

`threadlepy.commands` includes wrappers for Threadle process workflow,
inventory, file IO, layer editing, node editing, attributes, shortest paths,
degree and density, components, random generation, random walks, packing,
projection, filtering, subnetwork creation, and export utilities.

## Release Checklist

Before publishing a new PyPI release:

```bash
python3 -m compileall src/threadlepy scripts/test_commands.py
python3 -m json.tool docs/threadlepy_tutorial.ipynb > /tmp/threadlepy_tutorial_checked.json
python3 scripts/test_commands.py
python3 scripts/test_session.py
python3 -m build
python3 -m twine check dist/*
```

Use TestPyPI first when publishing a new release line.
