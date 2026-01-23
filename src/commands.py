from __future__ import annotations
from typing import Any, Optional, Union

from .client import call, ThreadleStruct, ThreadleName

NodeId = Union[int, str]


# --------------------
# Workdir
# --------------------
def get_workdir():
    cmd = "getwd"
    assign = None
    return call(cmd, locals(), assign=assign)

def set_workdir(dir: str):
    cmd = "setwd"
    assign = None
    return call(cmd, locals(), assign=assign)

# --------------------
# Meta
# --------------------
def inventory():
    cmd = "i"
    assign = None
    return call(cmd, locals(), assign=assign)

def info(structure: Union[str, ThreadleStruct]):
    cmd = "info"
    assign = None
    return call(cmd, locals(), assign=assign)

# ============================================
# Layer / Edge / Hyperedge / Affiliation ops
# ============================================

def add_aff(network: ThreadleName, layername: str, nodeid: NodeId, hypername: str,
            addmissingnode: bool = True, addmissingaffiliation: bool = True):
    cmd = "addaff"
    assign = None
    return call(cmd, locals(), assign=assign)


def remove_aff(network: ThreadleName, layername: str, nodeid: NodeId, hypername: str):
    cmd = "removeaff"
    assign = None
    
    return call(cmd, locals(), assign=assign)


def add_edge(network: ThreadleName, layername: str, node1id: NodeId, node2id: NodeId,
             value: int = 1, addmissingnodes: bool = True):
    cmd = "addedge"
    assign = None
    return call(cmd, locals(), assign=assign)


def remove_edge(network: ThreadleName, layername: str, node1id: NodeId, node2id: NodeId):
    cmd = "removeedge"
    assign = None
    return call(cmd, locals(), assign=assign)


def check_edge(network: ThreadleName, layername: str, node1id: NodeId, node2id: NodeId):
    cmd = "checkedge"
    assign = None
    return call(cmd, locals(), assign=assign)


def clear_layer(network: ThreadleName, layername: str):
    cmd = "clearlayer"
    assign = None
    return call(cmd, locals(), assign=assign)


def add_hyper(network: ThreadleName, layername: str, hypername: str,
              nodes: Optional[list[Any]] = None, addmissingnodes: bool = True):
    """
    Notes:
      - ThreadleR collapses node vectors with ';' and uses "" when None.
    """
    cmd = "addhyper"
    assign = None
    nodes = "" if nodes is None else ";".join(map(str, nodes))
    return call(cmd, locals(), assign=assign)


def remove_hyper(network: ThreadleName, layername: str, hypername: str):
    cmd = "removehyper"
    assign = None
    return call(cmd, locals(), assign=assign)


def add_layer(network: ThreadleName, layername: str, mode: int,
              directed: bool = False, valuetype: str = "binary", selfties: bool = False):
    """
    valuetype: "binary" or "valued"
    """
    if valuetype not in ("binary", "valued"):
        raise ValueError('valuetype must be "binary" or "valued".')
    cmd = "addlayer"
    assign = None
    return call(cmd, locals(), assign=assign)

def remove_layer(network: Union[str, ThreadleStruct], layername: str):
    cmd = "removelayer"
    assign = None
    return call(cmd, locals(), assign=assign)

# ============================================
# Nodeset / Node ops
# ============================================

def add_node(structure: ThreadleName, id: NodeId):
    cmd = "addnode"
    assign = None
    return call(cmd, locals(), assign=assign)


def remove_node(structure: ThreadleName, nodeid: NodeId):
    cmd = "removenode"
    assign = None
    return call(cmd, locals(), assign=assign)


def get_nbr_nodes(structure: ThreadleName):
    cmd = "getnbrnodes"
    assign = None
    return call(cmd, locals(), assign=assign)


def get_nodeid_by_index(structure: ThreadleName, index: int):
    cmd = "getnodeidbyindex"
    assign = None
    return call(cmd, locals(), assign=assign)


def get_random_node(structure: ThreadleName):
    cmd = "getrandomnode"
    assign = None
    return call(cmd, locals(), assign=assign)


# ============================================
# Attributes
# ============================================

def define_attr(structure: ThreadleName, attrname: str, attrtype: str = "int"):
    """
    attrtype: "int", "char", "float", or "bool"
    """
    if attrtype not in ("int", "char", "float", "bool"):
        raise ValueError('attrtype must be one of: "int", "char", "float", "bool".')
    cmd = "defineattr"
    assign = None
    return call(cmd, locals(), assign=assign)


def undefine_attr(structure: ThreadleName, attrname: str):
    cmd = "undefineattr"
    assign = None
    return call(cmd, locals(), assign=assign)


def get_attr(structure: ThreadleName, nodeid: NodeId, attrname: str):
    cmd = "getattr"
    assign = None
    return call(cmd, locals(), assign=assign)


def set_attr(structure: ThreadleName, nodeid: NodeId, attrname: str, attrvalue: Any):
    cmd = "setattr"
    assign = None
    return call(cmd, locals(), assign=assign)


def remove_attr(structure: ThreadleName, nodeid: NodeId, attrname: str):
    cmd = "removeattr"
    assign = None
    return call(cmd, locals(), assign=assign)


# ============================================
# Edge queries / paths / neighborhoods
# ============================================

def get_edge(network: ThreadleName, layername: str, node1id: NodeId, node2id: NodeId):
    cmd = "getedge"
    assign = None
    return call(cmd, locals(), assign=assign)


def get_node_alters(network: ThreadleName, nodeid: NodeId, layername: str = "",
                    direction: str = "both", unique: bool = False):
    """
    direction: "both", "in", "out"
    layername:
      - "" for all layers
      - if you pass multiple layer names, pre-join with ';' before calling this wrapper
    """
    if direction not in ("both", "in", "out"):
        raise ValueError('direction must be one of: "both", "in", "out".')
    cmd = "getnodealters"
    assign = None
    layername = "" if (layername is None or layername == "") else layername
    return call(cmd, locals(), assign=assign)


def get_random_alter(network: ThreadleName, nodeid: NodeId, layername: str = "",
                     direction: str = "both", balanced: bool = False):
    if direction not in ("both", "in", "out"):
        raise ValueError('direction must be one of: "both", "in", "out".')
    cmd = "getrandomalter"
    assign = None
    return call(cmd, locals(), assign=assign)


def shortest_path(network: ThreadleName, node1id: NodeId, node2id: NodeId, layername: str = ""):
    cmd = "shortestpath"
    assign = None
    layername = "" if layername is None else layername
    return call(cmd, locals(), assign=assign)


# ============================================
# Network measures / transforms
# ============================================

def degree(network: ThreadleName, layername: str, attrname: Optional[str] = None, direction: str = "in"):
    if direction not in ("in", "out", "both"):
        raise ValueError('direction must be one of: "in", "out", "both".')
    cmd = "degree"
    assign = None
    return call(cmd, locals(), assign=assign)


def density(network: ThreadleName, layername: str):
    cmd = "density"
    assign = None
    return call(cmd, locals(), assign=assign)


def dichotomize(network: ThreadleName, layername: str,
               cond: str = "ge", threshold: Any = 1,
               truevalue: Any = 1, falsevalue: Any = 0,
               newlayername: Optional[str] = None):
    """
    cond: "ge","eq","ne","gt","lt","le","isnull","notnull"
    """
    if cond not in ("ge", "eq", "ne", "gt", "lt", "le", "isnull", "notnull"):
        raise ValueError('cond must be one of: ge, eq, ne, gt, lt, le, isnull, notnull')
    cmd = "dichotomize"
    assign = None
    return call(cmd, locals(), assign=assign)


def components(network: ThreadleName, layname: str, attrname: str):
    cmd = "components"
    assign = None
    return call(cmd, locals(), assign=assign)

def symmetrize(network: Union[str, ThreadleStruct], layername: str, newlayername: Optional[str] = None):
    cmd = "symmetrize"
    assign = None
    return call(cmd, locals(), assign=assign)

# ============================================
# Creation / IO / lifecycle
# ============================================

def create_nodeset(name: str, createnodes: int = 0):
    cmd = "createnodeset"
    assign = name
    call(cmd, locals(), assign=assign)
    # Return a client-side handle (assumes you have Nodeset/ThreadleStruct-style wrappers)
    return ThreadleStruct(name=name)


def create_network(nodeset: ThreadleName, name: str):
    cmd = "createnetwork"
    assign = name
    call(cmd, locals(), assign=assign)
    return ThreadleStruct(name=name)


def load_file(name: str, file: str, type: str):
    """
    type: "network" or "nodeset"
    """
    cmd = "loadfile"
    assign = name
    call(cmd, locals(), assign=assign)

    # Return a client-side handle (replace with Network/Nodeset classes if you have them)
    if type == "network":
        return ThreadleStruct(name=name)
    if type == "nodeset":
        return ThreadleStruct(name=name)
    raise ValueError(f"Unknown type: {type}")


def save_file(structure: ThreadleName, file: str = ""):
    """
    If file is empty, ThreadleR defaults to "<structure>.tsv".
    """
    cmd = "savefile"
    assign = None
    if not file:
        file = f"{structure}.tsv"
    return call(cmd, locals(), assign=assign)


def import_layer(network: ThreadleName, layername: str, file: str,
                 format: str = "edgelist", sep: str = "\t", addmissingnodes: bool = False):
    """
    format: "edgelist" or "matrix"
    """
    if format not in ("edgelist", "matrix"):
        raise ValueError('format must be "edgelist" or "matrix".')
    cmd = "importlayer"
    assign = None
    return call(cmd, locals(), assign=assign)


def delete(structure: ThreadleName):
    cmd = "delete"
    assign = None
    return call(cmd, locals(), assign=assign)


def delete_all():
    cmd = "deleteall"
    assign = None
    return call(cmd, locals(), assign=assign)


# ============================================
# Subsetting / filtering
# ============================================

def filter_nodeset(name: str, nodeset: ThreadleName, attrname: str, cond: str, attrvalue: Any):
    cmd = "filter"
    assign = name
    call(cmd, locals(), assign=assign)
    return ThreadleStruct(name=name)


def subnet(name: str, network: ThreadleName, nodeset: ThreadleName):
    cmd = "subnet"
    assign = name
    call(cmd, locals(), assign=assign)
    return ThreadleStruct(name=name)


# ============================================
# Random generation / settings
# ============================================

def generate(network: ThreadleName, layername: str, type: str,
             p: Optional[float] = None, k: Optional[int] = None,
             beta: Optional[float] = None, m: Optional[int] = None):
    cmd = "generate"
    assign = None
    return call(cmd, locals(), assign=assign)


def setting(name: str, value: Any):
    cmd = "setting"
    assign = None
    return call(cmd, locals(), assign=assign)