from __future__ import annotations

import os
import inspect
import shutil
from importlib import resources
from typing import Any, Literal, Optional, Union

from .client import ThreadleName, ThreadleStruct, call, is_available as _client_is_available, raw_cmd, start, stop

NodeId = Union[int, str]
Condition = Literal["eq", "ne", "gt", "lt", "ge", "le", "isnull", "notnull"]
NumericCondition = Literal["eq", "ne", "gt", "lt", "ge", "le"]
Direction = Literal["both", "in", "out"]
AttrType = Literal["int", "char", "float", "bool", "string"]
LayerMode = Literal[1, 2, "1", "2"]
LayerValueType = Literal["binary", "valued"]
LayerFormat = Literal["edgelist", "matrix"]
StructureType = Literal["network", "nodeset"]
SymmetrizeMethod = Literal["max", "min", "minnonzero", "average", "sum", "product"]
ProjectMethod = Literal["count", "newman", "binary"]
GenerateType = Literal["er", "ws", "ba", "2mode"]

CONDITIONS: tuple[Condition, ...] = ("eq", "ne", "gt", "lt", "ge", "le", "isnull", "notnull")
NUMERIC_CONDITIONS: tuple[NumericCondition, ...] = ("eq", "ne", "gt", "lt", "ge", "le")
DIRECTIONS: tuple[Direction, ...] = ("both", "in", "out")
ATTR_TYPES: tuple[AttrType, ...] = ("int", "char", "float", "bool", "string")
LAYER_VALUE_TYPES: tuple[LayerValueType, ...] = ("binary", "valued")
LAYER_FORMATS: tuple[LayerFormat, ...] = ("edgelist", "matrix")
STRUCTURE_TYPES: tuple[StructureType, ...] = ("network", "nodeset")
SYMMETRIZE_METHODS: tuple[SymmetrizeMethod, ...] = ("max", "min", "minnonzero", "average", "sum", "product")
PROJECT_METHODS: tuple[ProjectMethod, ...] = ("count", "newman", "binary")
GENERATE_TYPES: tuple[GenerateType, ...] = ("er", "ws", "ba", "2mode")


def _check(value: str, allowed: tuple[str, ...], name: str) -> str:
    if value not in allowed:
        opts = ", ".join(repr(x) for x in allowed)
        raise ValueError(f"{name} must be one of: {opts}.")
    return value


def _collapse(values: Optional[Union[str, list[Any], tuple[Any, ...]]]) -> str:
    if values is None:
        return ""
    if isinstance(values, str):
        return values
    return ";".join(str(x) for x in values)


def _handle(name: str) -> ThreadleStruct:
    return ThreadleStruct(name=name)


# --------------------
# Process escape hatch
# --------------------
def is_available(path: Optional[str] = "threadle") -> bool:
    """Return whether the Threadle CLI executable can be found."""
    return _client_is_available(path)


def start_threadle(path: Optional[str] = None):
    """Start the Threadle CLI process in JSON mode."""
    return start(path)


def stop_threadle():
    """Stop the running Threadle CLI process."""
    return stop()


def cmd(
    command: Optional[str] = None,
    args: Optional[dict[str, Any]] = None,
    *,
    assign: Optional[str] = None,
    type: Optional[StructureType] = None,
    **kwargs: Any,
):
    """Send a raw Threadle command to the backend."""
    if command is None:
        command = kwargs.pop("cmd", None)
    elif "cmd" in kwargs:
        raise TypeError("Use either command= or cmd=, not both.")
    if kwargs:
        unknown = ", ".join(kwargs)
        raise TypeError(f"Unexpected keyword argument(s): {unknown}")
    if command is None:
        raise TypeError("cmd() missing required command name.")
    payload = raw_cmd(command, args, assign=assign)
    if assign is not None and type is not None:
        return _handle(assign)
    return payload


# --------------------
# Workdir / filesystem
# --------------------
def get_workdir():
    """Return Threadle's current working directory."""
    return call("getwd", locals())


def set_workdir(dir: str):
    """Set Threadle's current working directory."""
    return call("setwd", locals())


def sync_wd():
    """Set Threadle's working directory to the current Python working directory."""
    return set_workdir(os.getcwd())


def dir(path: Optional[str] = None):
    """List files in a Threadle-visible directory."""
    return call("dir", locals())


def stage_examples_to_wd(folder: str = "threadle_examples", overwrite: bool = True) -> str:
    """Copy bundled example files into a local folder."""
    dest = os.path.expanduser(folder)
    if not os.path.isabs(dest):
        dest = os.path.join(os.getcwd(), dest)
    os.makedirs(dest, exist_ok=True)

    src = resources.files("threadlepy").joinpath("Examples")
    for item in src.iterdir():
        if item.is_file():
            target = os.path.join(dest, item.name)
            if overwrite or not os.path.exists(target):
                with resources.as_file(item) as p:
                    shutil.copy2(p, target)
    return os.path.abspath(dest)


# --------------------
# Meta
# --------------------
def inventory():
    """Return the objects currently stored in the Threadle session."""
    return call("i", locals())


def i():
    """Return the objects currently stored in the Threadle session."""
    return inventory()


def info(structure: ThreadleName):
    """Return metadata for a Threadle network or nodeset."""
    return call("info", locals())


def preview(structure: ThreadleName):
    """Return a human-readable preview of a Threadle network or nodeset."""
    return call("preview", locals())


# ============================================
# Layer / Edge / Hyperedge / Affiliation ops
# ============================================
def add_aff(
    network: ThreadleName,
    layername: str,
    nodeid: NodeId,
    hypername: str,
    addmissingnode: bool = True,
    addmissinghyperedge: bool = True,
    addmissingaffiliation: Optional[bool] = None,
):
    """Add a node-to-hyperedge affiliation in a two-mode layer."""
    if addmissingaffiliation is not None:
        addmissinghyperedge = addmissingaffiliation
    return call("addaff", locals(), drop=("addmissingaffiliation",))


def remove_aff(network: ThreadleName, layername: str, nodeid: NodeId, hypername: str):
    """Remove a node-to-hyperedge affiliation from a two-mode layer."""
    return call("removeaff", locals())


def add_edge(
    network: ThreadleName,
    layername: str,
    node1id: NodeId,
    node2id: NodeId,
    value: Any = 1,
    addmissingnodes: bool = True,
):
    """Add an edge between two nodes in a one-mode layer."""
    return call("addedge", locals())


def remove_edge(network: ThreadleName, layername: str, node1id: NodeId, node2id: NodeId):
    """Remove an edge between two nodes from a one-mode layer."""
    return call("removeedge", locals())


def check_edge(network: ThreadleName, layername: str, node1id: NodeId, node2id: NodeId):
    """Return whether two nodes are connected in a layer."""
    return call("checkedge", locals())


def get_edge(network: ThreadleName, layername: str, node1id: NodeId, node2id: NodeId):
    """Return the value of an edge between two nodes."""
    return call("getedge", locals())


def get_random_edge(network: ThreadleName, layername: str, maxattempts: int = 100):
    """Return a random edge from a layer."""
    return call("getrandomedge", locals())


def get_all_edges(network: ThreadleName, layername: str, offset: int = 0, limit: int = 1000):
    """Return edges from a one-mode layer with optional pagination."""
    return call("getalledges", locals())


def clear_layer(network: ThreadleName, layername: str):
    """Remove all edges or hyperedges from a layer while keeping the layer."""
    return call("clearlayer", locals())


def add_hyper(
    network: ThreadleName,
    layername: str,
    hypername: str,
    nodes: Optional[Union[list[Any], tuple[Any, ...], str]] = None,
    addmissingnodes: bool = True,
):
    """Add a hyperedge to a two-mode layer."""
    nodes = _collapse(nodes)
    return call("addhyper", locals())


def remove_hyper(network: ThreadleName, layername: str, hypername: str):
    """Remove a hyperedge from a two-mode layer."""
    return call("removehyper", locals())


def get_all_hyperedges(network: ThreadleName, layername: str, offset: int = 0, limit: int = 1000):
    """Return hyperedges from a two-mode layer with optional pagination."""
    return call("getallhyperedges", locals())


def get_hyperedge_nodes(network: ThreadleName, layername: str, hypername: str):
    """Return the nodes affiliated with a hyperedge."""
    return call("gethyperedgenodes", locals())


def get_node_hyperedges(network: ThreadleName, layername: str, nodeid: NodeId):
    """Return the hyperedges affiliated with a node."""
    return call("getnodehyperedges", locals())


def add_layer(
    network: ThreadleName,
    layername: str,
    mode: LayerMode,
    directed: bool = False,
    valuetype: LayerValueType = "binary",
    selfties: bool = False,
):
    """Add a one-mode or two-mode relational layer to a network."""
    if str(mode) not in ("1", "2"):
        raise ValueError("mode must be 1 or 2.")
    _check(valuetype, LAYER_VALUE_TYPES, "valuetype")
    return call("addlayer", locals())


def remove_layer(network: ThreadleName, layername: str):
    """Remove a relational layer and its ties from a network."""
    return call("removelayer", locals())


def import_layer(
    network: ThreadleName,
    layername: str,
    file: str,
    format: LayerFormat = "edgelist",
    node1col: int = 0,
    node2col: int = 1,
    valuecol: int = 2,
    nodecol: int = 0,
    affcol: int = 1,
    header: bool = False,
    sep: str = "\t",
    addmissingnodes: bool = False,
):
    """Import ties into an existing network layer from a file."""
    _check(format, LAYER_FORMATS, "format")
    return call("importlayer", locals())


def export_layer(network: ThreadleName, layername: str, file: str, header: bool = True, sep: str = "\t"):
    """Export a network layer as an edge list file."""
    return call("exportlayer", locals())


# ============================================
# Nodeset / Node ops
# ============================================
def add_node(structure: ThreadleName, nodeid: Optional[NodeId] = None, id: Optional[NodeId] = None):
    """Add a node to a nodeset or to the nodeset of a network."""
    if nodeid is None:
        nodeid = id
    if nodeid is None:
        raise TypeError("add_node() missing required argument: 'nodeid'")
    return call("addnode", locals(), drop=("id",))


def remove_node(structure: ThreadleName, nodeid: NodeId):
    """Remove a node from a nodeset or network nodeset."""
    return call("removenode", locals())


def get_nbr_nodes(structure: ThreadleName):
    """Return the number of nodes in a network or nodeset."""
    return call("getnbrnodes", locals())


def get_all_nodes(structure: ThreadleName, offset: int = 0, limit: int = 1000):
    """Return nodes from a network or nodeset with optional pagination."""
    return call("getallnodes", locals())


def get_nodeid_by_index(structure: ThreadleName, index: int):
    """Return the node id at an index position."""
    return call("getnodeidbyindex", locals())


def get_random_node(structure: ThreadleName):
    """Return a random node id from a network or nodeset."""
    return call("getrandomnode", locals())


# ============================================
# Attributes
# ============================================
def define_attr(structure: ThreadleName, attrname: str, attrtype: AttrType = "int"):
    """Define a node attribute on a network or nodeset."""
    _check(attrtype, ATTR_TYPES, "attrtype")
    return call("defineattr", locals())


def undefine_attr(structure: ThreadleName, attrname: str):
    """Remove a node attribute definition and its stored values."""
    return call("undefineattr", locals())


def get_attr(structure: ThreadleName, nodeid: NodeId, attrname: str):
    """Return one node attribute value."""
    return call("getattr", locals())


def get_attrs(structure: ThreadleName, nodes: Union[str, list[NodeId], tuple[NodeId, ...]], attrname: str):
    """Return one attribute value for multiple nodes."""
    nodes = _collapse(nodes)
    return call("getattrs", locals())


def get_attr_summary(structure: ThreadleName, attrname: str):
    """Return summary statistics for a node attribute."""
    return call("getattrsummary", locals())


def set_attr(structure: ThreadleName, nodeid: NodeId, attrname: str, attrvalue: Any):
    """Set one node attribute value."""
    return call("setattr", locals())


def remove_attr(structure: ThreadleName, nodeid: NodeId, attrname: str):
    """Remove one node attribute value."""
    return call("removeattr", locals())


def generate_attr(
    structure: ThreadleName,
    attrname: str,
    attrtype: AttrType = "int",
    min: Optional[Any] = None,
    max: Optional[Any] = None,
    p: float = 0.5,
    chars: str = "m;f;o",
    values: Optional[Union[str, list[Any], tuple[Any, ...]]] = None,
):
    """Generate random values for a node attribute."""
    _check(attrtype, ATTR_TYPES, "attrtype")
    if attrtype == "int":
        min = 0 if min is None else min
        max = 100 if max is None else max
    elif attrtype == "float":
        min = 0.0 if min is None else min
        max = 1.0 if max is None else max
    values = _collapse(values) if values is not None else None
    return call("generateattr", locals())


# ============================================
# Edge queries / paths / neighborhoods
# ============================================
def get_node_alters(
    network: ThreadleName,
    nodeid: NodeId,
    layernames: Optional[Union[str, list[str], tuple[str, ...]]] = "",
    direction: Direction = "out",
    unique: bool = True,
    layername: Optional[Union[str, list[str], tuple[str, ...]]] = None,
):
    """Return alters of a node within one or more layers."""
    _check(direction, DIRECTIONS, "direction")
    if layername is not None and not layernames:
        layernames = layername
    layernames = _collapse(layernames)
    return call("getnodealters", locals(), drop=("layername",))


def get_random_alter(
    network: ThreadleName,
    nodeid: NodeId,
    layernames: Optional[Union[str, list[str], tuple[str, ...]]] = "",
    direction: Direction = "both",
    balanced: bool = False,
    weighted: bool = False,
    layername: Optional[Union[str, list[str], tuple[str, ...]]] = None,
):
    """Return a random alter of a node."""
    _check(direction, DIRECTIONS, "direction")
    if layername is not None and not layernames:
        layernames = layername
    layernames = _collapse(layernames)
    return call("getrandomalter", locals(), drop=("layername",))


def get_degree(
    network: ThreadleName,
    nodeid: NodeId,
    layernames: Optional[Union[str, list[str], tuple[str, ...]]] = None,
    direction: Direction = "out",
    unique: bool = True,
    layername: Optional[Union[str, list[str], tuple[str, ...]]] = None,
):
    """Return the degree of a node within one or more layers."""
    _check(direction, DIRECTIONS, "direction")
    if layername is not None and not layernames:
        layernames = layername
    layernames = _collapse(layernames)
    return call("getdegree", locals(), drop=("layername",))


def shortest_path(
    network: ThreadleName,
    node1id: NodeId,
    node2id: NodeId,
    layernames: Optional[Union[str, list[str], tuple[str, ...]]] = None,
    layername: Optional[Union[str, list[str], tuple[str, ...]]] = None,
):
    """Return the shortest path distance between two nodes."""
    if layername is not None and not layernames:
        layernames = layername
    layernames = _collapse(layernames)
    return call("shortestpath", locals(), drop=("layername",))


def shortest_paths(
    name: str,
    network: ThreadleName,
    attrname: str,
    layernames: Optional[Union[str, list[str], tuple[str, ...]]] = None,
    layername: Optional[Union[str, list[str], tuple[str, ...]]] = None,
):
    """Compute category-level average shortest paths and return a result network handle."""
    if layername is not None and not layernames:
        layernames = layername
    layernames = _collapse(layernames)
    call("shortestpaths", locals(), assign=name, drop=("layername",))
    return _handle(name)


# ============================================
# Network measures / transforms
# ============================================
def degree(network: ThreadleName, layername: str, attrname: Optional[str] = None, direction: Direction = "out"):
    """Compute node degree values for a layer."""
    _check(direction, DIRECTIONS, "direction")
    return call("degree", locals())


def density(network: ThreadleName, layername: str, samplesize: int = 200):
    """Compute or estimate the density of a layer."""
    return call("density", locals())


def dichotomize(
    network: ThreadleName,
    layername: str,
    cond: NumericCondition = "ge",
    threshold: Any = 1,
    truevalue: Any = 1,
    falsevalue: Any = 0,
    newlayername: Optional[str] = None,
):
    """Create a binary layer by thresholding a valued one-mode layer."""
    _check(cond, NUMERIC_CONDITIONS, "cond")
    return call("dichotomize", locals())


def components(
    network: ThreadleName,
    layername: Optional[str] = None,
    attrname: Optional[str] = None,
    layname: Optional[str] = None,
):
    """Compute connected components for a network layer."""
    if layername is None:
        layername = layname
    if layername is None:
        raise TypeError("components() missing required argument: 'layername'")
    return call("components", locals(), drop=("layname",))


def symmetrize(
    network: ThreadleName,
    layername: str,
    method: SymmetrizeMethod = "max",
    newlayername: Optional[str] = None,
):
    """Create a symmetric version of a one-mode layer."""
    _check(method, SYMMETRIZE_METHODS, "method")
    return call("symmetrize", locals())


def project_two_mode(
    network: ThreadleName,
    layername: str,
    method: ProjectMethod = "count",
    newlayername: Optional[str] = None,
):
    """Project a two-mode layer to a one-mode layer."""
    _check(method, PROJECT_METHODS, "method")
    return call("projecttwomode", locals())


def pack(network: ThreadleName, layername: Optional[str] = None):
    """Convert one or all dynamic layers to a static memory-efficient representation."""
    return call("pack", locals())


def unpack(network: ThreadleName, layername: Optional[str] = None):
    """Convert one or all static layers back to an editable representation."""
    return call("unpack", locals())


# ============================================
# Creation / IO / lifecycle
# ============================================
def create_nodeset(var: str, name: Optional[str] = None, createnodes: int = 0):
    """Create a nodeset and return its Threadle handle."""
    call("createnodeset", locals(), assign=var)
    return _handle(var)


def create_network(var: str, nodeset: ThreadleName, name: Optional[str] = None):
    """Create a network from a nodeset and return its Threadle handle."""
    call("createnetwork", locals(), assign=var)
    return _handle(var)


def load_file(name: str, file: str, type: StructureType, pack: bool = False):
    """Load a nodeset or network file and return its Threadle handle."""
    _check(type, STRUCTURE_TYPES, "type")
    file2 = os.path.expanduser(file)
    old_wd = None
    if os.path.dirname(file2):
        dir2 = os.path.dirname(file2)
        if dir2 and dir2 != ".":
            old_wd = get_workdir()
            set_workdir(os.path.abspath(dir2))
            file2 = os.path.basename(file2)
    try:
        raw_cmd("loadfile", {"file": file2, "type": type, "pack": pack}, assign=name)
    finally:
        if old_wd is not None:
            set_workdir(old_wd)
    return _handle(name)


def save_file(structure: ThreadleName, file: str = ""):
    """Save a Threadle network or nodeset to disk."""
    return call("savefile", locals())


def load_script(file: str):
    """Load and run a Threadle script file."""
    return call("loadscript", locals())


def load_examples(
    examples: Union[str, list[str], tuple[str, ...]] = ("mynet", "lazega"),
    assign: bool = True,
    set_workdir_to_examples: bool = True,
    set_workdir: Optional[bool] = None,
):
    """Load bundled example datasets and return their Threadle handles."""
    if set_workdir is not None:
        set_workdir_to_examples = set_workdir

    specs = {
        "mynet": ("mynet_nodeset", "mynet_nodesetfile.tsv", "mynet", "mynet.tsv"),
        "lazega": ("lazega_nodeset", "lazega_nodes.tsv", "lazega", "lazega.tsv"),
        "lazega_female": (
            "lazega_female_nodeset",
            "lazega_female_nodeset.tsv",
            "lazega_female",
            "lazega_female.tsv",
        ),
        "dscw": ("dscw_nodeset", "dscw_nodeset.tsv", "dscw", "dscw.tsv"),
    }
    selected = [examples] if isinstance(examples, str) else list(examples)
    if selected == ["all"]:
        selected = list(specs)
    unknown = [x for x in selected if x not in specs]
    if unknown:
        raise ValueError(f"Unknown example dataset(s): {', '.join(unknown)}")

    caller_frame = inspect.currentframe().f_back
    old_workdir = None

    with resources.as_file(resources.files("threadlepy").joinpath("Examples")) as ext:
        if set_workdir_to_examples:
            old_workdir = get_workdir()
            globals()["set_workdir"](str(ext))

        try:
            out: dict[str, ThreadleStruct] = {}
            for example in selected:
                ns_name, ns_file, net_name, net_file = specs[example]
                out[ns_name] = load_file(ns_name, os.path.join(str(ext), ns_file), type="nodeset")
                out[net_name] = load_file(net_name, os.path.join(str(ext), net_file), type="network")

            if assign and caller_frame is not None:
                caller_frame.f_globals.update(out)
                caller_frame.f_locals.update(out)

            return out
        finally:
            if old_workdir is not None:
                globals()["set_workdir"](old_workdir)


def export(network: ThreadleName, file: str, layername: str, format: str = "gexf"):
    """Export a network layer to an external graph format."""
    return call("export", locals())


def delete(structure: ThreadleName):
    """Delete a Threadle structure from the current session."""
    return call("delete", locals())


def delete_all():
    """Delete all Threadle structures from the current session."""
    return call("deleteall", locals())


# ============================================
# Subsetting / filtering
# ============================================
def filter(name: str, nodeset: ThreadleName, attrname: str, cond: Condition, attrvalue: Any = None):
    """Create a filtered nodeset from node attribute values."""
    _check(cond, CONDITIONS, "cond")
    call("filter", locals(), assign=name)
    return _handle(name)


def filter_nodeset(name: str, nodeset: ThreadleName, attrname: str, cond: Condition, attrvalue: Any = None):
    """Alias for filter."""
    return filter(name, nodeset, attrname, cond, attrvalue)


def subnet(name: str, network: ThreadleName, nodeset: ThreadleName):
    """Create a subnetwork induced by a nodeset."""
    call("subnet", locals(), assign=name)
    return _handle(name)


# ============================================
# Random generation / random walks / settings
# ============================================
def generate(
    network: ThreadleName,
    layername: str,
    type: GenerateType,
    p: Optional[float] = None,
    k: Optional[int] = None,
    beta: Optional[float] = None,
    m: Optional[int] = None,
    h: Optional[int] = None,
    a: Optional[float] = None,
):
    """Generate random ties in a network layer."""
    _check(type, GENERATE_TYPES, "type")
    return call("generate", locals())


def rwdistances(
    name: str,
    network: ThreadleName,
    attrname: str,
    maxsteps: int,
    layernames: Optional[Union[str, list[str], tuple[str, ...]]] = None,
    walkfactor: float = 1.0,
    balanced: bool = False,
    weighted: bool = False,
    backtrack: bool = False,
    savesteps: bool = False,
    layername: Optional[Union[str, list[str], tuple[str, ...]]] = None,
):
    """Estimate category distances with random walks and return a result network handle."""
    if layername is not None and not layernames:
        layernames = layername
    layernames = _collapse(layernames)
    call("rwdistances", locals(), assign=name, drop=("layername",))
    return _handle(name)


def rwfpt(
    name: str,
    network: ThreadleName,
    attrname: str,
    maxsteps: int,
    layernames: Optional[Union[str, list[str], tuple[str, ...]]] = None,
    walkfactor: float = 1.0,
    minpairobs: int = 10,
    balanced: bool = False,
    weighted: bool = False,
    layername: Optional[Union[str, list[str], tuple[str, ...]]] = None,
):
    """Estimate category mean first-passage times with random walks and return a result network handle."""
    if layername is not None and not layernames:
        layernames = layername
    layernames = _collapse(layernames)
    call("rwfpt", locals(), assign=name, drop=("layername",))
    return _handle(name)


def random_seed(seed: int = 6031769):
    """Set Threadle's random seed."""
    return call("randomseed", locals())


def setting(name: str, value: Any):
    """Set a Threadle backend setting or a threadlepy runtime setting."""
    if name.lower() == "verbose":
        from . import client

        if isinstance(value, str):
            client.configure(print_messages=value.strip().lower() != "false")
        else:
            client.configure(print_messages=bool(value))
        return None
    return call("setting", locals())


def _install_threadle_r_aliases() -> None:
    """Expose th_* aliases for users moving between threadleR and threadlepy."""
    skip = {"Any", "Optional", "Union", "ThreadleStruct"}
    for name, obj in list(globals().items()):
        if name in skip or name.startswith("_") or name.startswith("th_"):
            continue
        if callable(obj) and getattr(obj, "__module__", None) == __name__:
            globals()[f"th_{name}"] = obj


_install_threadle_r_aliases()

__all__ = sorted(
    name
    for name, obj in globals().items()
    if callable(obj) and not name.startswith("_") and getattr(obj, "__module__", None) == __name__
)
