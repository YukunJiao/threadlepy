# threadlepy

Python client for the Threadle CLI JSON interface.

`threadlepy` starts a Threadle subprocess and exposes Python wrappers for core Threadle workflows.

## Installation

```bash
pip install threadlepy
```

Requirements:

- Python 3.9+
- A working `threadle` executable available on `PATH`

## Quick Start

```python
import threadlepy
import threadlepy.commands as th

with threadlepy.session(timeout=3600):
    examples = th.load_examples("lazega")
    lazega = examples["lazega"]

    print(th.info(lazega))

    path = th.shortest_path(
        lazega,
        node1id=1,
        node2id=23,
        layernames="friends",
    )

    print(path)
```

If `threadle` is not on `PATH`, pass the executable path explicitly:

```python
threadlepy.start("/full/path/to/threadle")
```

## Documentation

For more examples and workflows, see:

```text
docs/threadlepy_tutorial.ipynb
```