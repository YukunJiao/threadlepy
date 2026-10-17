#!/usr/bin/env python3
"""End-to-end threadlepy command workflow using bundled example data.

Usage:
    python scripts/test_all_commands_example_data.py
    python scripts/test_all_commands_example_data.py --threadle /full/path/to/threadle
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import threadlepy
import threadlepy.commands as th


def show(label: str, fn: Callable[[], Any]) -> Any:
    print(f"\n>>> {label}", flush=True)
    value = fn()
    if value is not None:
        text = repr(value)
        if len(text) > 1000:
            text = text[:997] + "..."
        print(text, flush=True)
    else:
        print("None", flush=True)
    return value


def run(threadle_path: str | None = None, *, timeout: float = 1800.0) -> int:
    path = threadle_path or "threadle"
    if not threadlepy.is_available(path):
        print(
            "SKIP: Threadle CLI was not found. Install `threadle`, add it to PATH, "
            "or pass --threadle /full/path/to/threadle.",
            file=sys.stderr,
        )
        return 77

    root_dir = Path.cwd()
    example_dir = root_dir / "threadle_examples"
    outputs_dir = root_dir / "threadle_outputs"
    example_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    threadlepy.configure(print_commands=False, print_messages=False, timeout=timeout)

    show("stage examples", lambda: th.stage_examples_to_wd(str(example_dir), overwrite=True))
    show("is_available", lambda: threadlepy.is_available(path))

    threadlepy.start(threadle_path)
    try:
        show("python cwd", Path.cwd)
        show("threadle initial workdir", th.get_workdir)

        # Load bundled example data from the staged example folder.
        show("set workdir to staged examples", lambda: th.set_workdir(str(example_dir)))
        mynet_nodeset = show(
            "load mynet_nodeset",
            lambda: th.load_file("mynet_nodeset", "mynet_nodesetfile.tsv", type="nodeset"),
        )
        mynet = show("load mynet", lambda: th.load_file("mynet", "mynet.tsv", type="network"))
        lazega_nodeset = show(
            "load lazega_nodeset",
            lambda: th.load_file("lazega_nodeset", "lazega_nodes.tsv", type="nodeset"),
        )
        lazega = show("load lazega", lambda: th.load_file("lazega", "lazega.tsv", type="network"))
        example_data = {
            "mynet_nodeset": mynet_nodeset,
            "mynet": mynet,
            "lazega_nodeset": lazega_nodeset,
            "lazega": lazega,
        }
        show("example data names", lambda: list(example_data))
        show("threadle staged workdir", th.get_workdir)
        show("dir", th.dir)

        show("inventory", th.i)
        show("info mynet", lambda: th.info(mynet))
        show("preview mynet", lambda: th.preview(mynet))
        show("raw cmd info", lambda: th.cmd("info", args={"structure": mynet}))

        # Explore nodes, attributes, one-mode ties, and two-mode affiliations.
        show("mynet node count", lambda: th.get_nbr_nodes(mynet))
        show("mynet nodes", lambda: th.get_all_nodes(mynet, offset=0, limit=8))
        show("first node", lambda: th.get_nodeid_by_index(mynet, index=0))
        show("random node", lambda: th.get_random_node(mynet))
        show("gender 123", lambda: th.get_attr(mynet_nodeset, nodeid=123, attrname="gender"))
        show("some genders", lambda: th.get_attrs(mynet_nodeset, nodes=[123, 234, 345], attrname="gender"))
        show("gender summary", lambda: th.get_attr_summary(mynet_nodeset, attrname="gender"))

        show("trade 123 345", lambda: th.get_edge(mynet, "trade", node1id=123, node2id=345))
        show("has kinship", lambda: th.check_edge(mynet, "kinship", node1id=123, node2id=345))
        show("trade edges", lambda: th.get_all_edges(mynet, "trade", offset=0, limit=10))
        show("random trade edge", lambda: th.get_random_edge(mynet, "trade"))
        show(
            "alters 345",
            lambda: th.get_node_alters(mynet, nodeid=345, layernames="trade", direction="both"),
        )
        show(
            "degree 345",
            lambda: th.get_degree(mynet, nodeid=345, layernames="trade", direction="both"),
        )
        show(
            "random alter 345",
            lambda: th.get_random_alter(mynet, nodeid=345, layernames="trade", direction="both"),
        )
        show("density kinship", lambda: th.density(mynet, "kinship"))

        show("work hyperedges", lambda: th.get_all_hyperedges(mynet, "work", offset=0, limit=10))
        show("ias nodes", lambda: th.get_hyperedge_nodes(mynet, "work", hypername="ias"))
        show("node 123 hyperedges", lambda: th.get_node_hyperedges(mynet, "work", nodeid=123))

        # Derive structures from the example data.
        female_nodeset = show(
            "filter female nodeset",
            lambda: th.filter("female_nodeset", mynet_nodeset, "gender", cond="eq", attrvalue="f"),
        )
        female_mynet = show("subnet female mynet", lambda: th.subnet("female_mynet", mynet, female_nodeset))
        show("info female nodeset", lambda: th.info(female_nodeset))
        show("info female mynet", lambda: th.info(female_mynet))

        show("components kinship", lambda: th.components(mynet, "kinship", attrname="kinship_component"))
        show("degree kinship", lambda: th.degree(mynet, "kinship", attrname="kinship_degree", direction="both"))
        show("kinship degree summary", lambda: th.get_attr_summary(mynet, "kinship_degree"))

        show(
            "shortest path 123 to 567",
            lambda: th.shortest_path(mynet, node1id=123, node2id=567, layernames="kinship"),
        )
        show(
            "shortest paths for pairs",
            lambda: th.shortest_paths(mynet, node1ids=[123, 567], node2ids=[567, 123], layernames="kinship"),
        )
        gender_shortest_paths = show(
            "shortest paths by gender",
            lambda: th.shortest_paths_attributes("gender_shortest_paths", mynet, attrname="gender", layernames="kinship"),
        )
        show("info gender shortest paths", lambda: th.info(gender_shortest_paths))

        show("symmetrize trade", lambda: th.symmetrize(mynet, "trade", method="max", newlayername="trade_sym"))
        show(
            "dichotomize trade",
            lambda: th.dichotomize(
                mynet,
                "trade",
                cond="ge",
                threshold=1000,
                truevalue=1,
                falsevalue=0,
                newlayername="trade_hi",
            ),
        )
        show("project work", lambda: th.project_two_mode(mynet, "work", method="count", newlayername="work_projected"))
        show("trade_sym edge", lambda: th.get_edge(mynet, "trade_sym", 123, 345))
        show("trade_hi edge", lambda: th.get_edge(mynet, "trade_hi", 890, 234))
        show("work_projected edge", lambda: th.get_edge(mynet, "work_projected", 123, 456))

        show("pack kinship", lambda: th.pack(mynet, layername="kinship"))
        show("unpack kinship", lambda: th.unpack(mynet, layername="kinship"))

        # Build and edit a small network.
        lab_nodes = show("create lab nodes", lambda: th.create_nodeset("lab_nodes", name="Lab nodes", createnodes=5))
        lab_net = show("create lab net", lambda: th.create_network("lab_net", lab_nodes, name="Lab network"))

        show("add node 10", lambda: th.add_node(lab_nodes, nodeid=10))
        show("lab nodes after add", lambda: th.get_all_nodes(lab_nodes, offset=0, limit=20))
        show("remove node 10", lambda: th.remove_node(lab_nodes, nodeid=10))

        show("add friendship", lambda: th.add_layer(lab_net, "friendship", mode=1, directed=False, valuetype="binary", selfties=False))
        show("add events", lambda: th.add_layer(lab_net, "events", mode=2))
        show("add edge 1 2", lambda: th.add_edge(lab_net, "friendship", node1id=1, node2id=2))
        show("add edge 2 3", lambda: th.add_edge(lab_net, "friendship", node1id=2, node2id=3))
        show("check friendship edge", lambda: th.check_edge(lab_net, "friendship", 1, 2))
        show("friendship edges", lambda: th.get_all_edges(lab_net, "friendship", offset=0, limit=10))
        show("remove edge 2 3", lambda: th.remove_edge(lab_net, "friendship", node1id=2, node2id=3))

        show("add edge 3 4", lambda: th.add_edge(lab_net, "friendship", node1id=3, node2id=4))
        show("random friendship edge", lambda: th.get_random_edge(lab_net, "friendship"))
        show("clear friendship", lambda: th.clear_layer(lab_net, "friendship"))
        show("friendship edges after clear", lambda: th.get_all_edges(lab_net, "friendship", offset=0, limit=10))

        show("add seminar hyperedge", lambda: th.add_hyper(lab_net, "events", hypername="seminar", nodes=[1, 2]))
        show("add seminar affiliation", lambda: th.add_aff(lab_net, "events", nodeid=3, hypername="seminar"))
        show("seminar nodes", lambda: th.get_hyperedge_nodes(lab_net, "events", "seminar"))
        show("node 3 hyperedges", lambda: th.get_node_hyperedges(lab_net, "events", 3))
        show("remove seminar affiliation", lambda: th.remove_aff(lab_net, "events", nodeid=3, hypername="seminar"))
        show("remove seminar", lambda: th.remove_hyper(lab_net, "events", hypername="seminar"))

        show("add temporary layer", lambda: th.add_layer(lab_net, "temporary", mode=1))
        show("remove temporary layer", lambda: th.remove_layer(lab_net, "temporary"))

        show("define score", lambda: th.define_attr(lab_nodes, "score", "int"))
        show("set score", lambda: th.set_attr(lab_nodes, nodeid=1, attrname="score", attrvalue=7))
        show("get score", lambda: th.get_attr(lab_nodes, 1, "score"))
        show("remove score", lambda: th.remove_attr(lab_nodes, nodeid=1, attrname="score"))
        show("undefine score", lambda: th.undefine_attr(lab_nodes, "score"))

        show("generate random_score", lambda: th.generate_attr(lab_nodes, "random_score", attrtype="int", min=1, max=10))
        show("random_score summary", lambda: th.get_attr_summary(lab_nodes, "random_score"))

        # Generate a random layer and run random-walk commands.
        random_nodes = show("create random nodes", lambda: th.create_nodeset("random_nodes", createnodes=20))
        random_net = show("create random net", lambda: th.create_network("random_net", random_nodes))
        show("add er_layer", lambda: th.add_layer(random_net, "er_layer", mode=1, directed=False, valuetype="binary"))
        show("generate er_layer", lambda: th.generate(random_net, "er_layer", type="er", p=1))
        show("er_layer edges", lambda: th.get_all_edges(random_net, "er_layer", offset=0, limit=10))

        walk_nodes = show("create walk nodes", lambda: th.create_nodeset("walk_nodes", createnodes=6))
        walk_net = show("create walk net", lambda: th.create_network("walk_net", walk_nodes))
        show("add walk layer", lambda: th.add_layer(walk_net, "walk_layer", mode=1, directed=False, valuetype="binary"))
        for node1, node2 in [(1, 2), (2, 3), (3, 4), (4, 5)]:
            show(f"add walk edge {node1}-{node2}", lambda node1=node1, node2=node2: th.add_edge(walk_net, "walk_layer", node1, node2))
        show("define group", lambda: th.define_attr(walk_net, "group", "int"))
        for node in range(1, 6):
            show(
                f"set group {node}",
                lambda node=node: th.set_attr(walk_net, nodeid=node, attrname="group", attrvalue=1 if node <= 2 else 2),
            )

        rw_fpt = show(
            "rw fpt",
            lambda: th.rwfpt(
                "rw_fpt",
                walk_net,
                attrname="group",
                maxsteps=30,
                layernames="walk_layer",
                walkfactor=0.5,
                minpairobs=1,
                balanced=False,
                weighted=False,
            ),
        )
        show("info rw fpt", lambda: th.info(rw_fpt))
        rw_fpt_hist = show(
            "rw fpt with histograms",
            lambda: th.rwfpt(
                "rw_fpt_hist",
                walk_net,
                attrname="group",
                maxsteps=30,
                layernames="walk_layer",
                walkfactor=0.5,
                minpairobs=1,
                balanced=False,
                weighted=False,
                return_histograms=True,
            ),
        )
        show(
            "info rw fpt histogram network",
            lambda: th.info(rw_fpt_hist["network"] if isinstance(rw_fpt_hist, dict) else rw_fpt_hist),
        )

        # Miscellaneous session helpers.
        show("setting verbose false", lambda: th.setting("verbose", False))
        show("setting verbose string false", lambda: th.setting("verbose", "false"))
        show("setting nodecache true", lambda: th.setting("nodecache", True))
        show("setting nodecache false", lambda: th.setting("nodecache", False))
        show("random seed", lambda: th.random_seed(42))
        show("sync wd", th.sync_wd)

        # Export, save, import, and load a Threadle script.
        kinship_edges_file = outputs_dir / "mynet_kinship_edges.tsv"
        mynet_gexf_file = outputs_dir / "mynet_kinship.gexf"
        mynet_saved_file = outputs_dir / "mynet_saved.tsv"

        show("export kinship layer", lambda: th.export_layer(mynet, "kinship", file=str(kinship_edges_file), header=True, sep="\t"))
        show("export kinship gexf", lambda: th.export(mynet, format="gexf", file=str(mynet_gexf_file), layername="kinship"))
        show("save mynet", lambda: th.save_file(mynet, file=str(mynet_saved_file)))
        for file in (kinship_edges_file, mynet_gexf_file, mynet_saved_file):
            if not file.exists():
                raise FileNotFoundError(f"Expected output file was not created: {file}")

        mynet_nodeset_copy = show(
            "load mynet nodeset copy",
            lambda: th.load_file("mynet_nodeset_copy", str(example_dir / "mynet_nodesetfile.tsv"), type="nodeset"),
        )
        show("info mynet nodeset copy", lambda: th.info(mynet_nodeset_copy))

        import_nodes = show("create import nodes", lambda: th.create_nodeset("import_nodes", createnodes=3))
        import_net = show("create import net", lambda: th.create_network("import_net", import_nodes))
        show("add imported_edges layer", lambda: th.add_layer(import_net, "imported_edges", mode=1, directed=False, valuetype="valued"))
        edge_file = outputs_dir / "import_edges.tsv"
        edge_file.write_text("1\t2\t4\n2\t3\t5\n", encoding="utf-8")
        show(
            "import edges",
            lambda: th.import_layer(
                import_net,
                "imported_edges",
                file=str(edge_file),
                format="edgelist",
                node1col=0,
                node2col=1,
                valuecol=2,
                header=False,
                sep="\t",
                addmissingnodes=False,
            ),
        )
        show("imported edge value", lambda: th.get_edge(import_net, "imported_edges", 1, 2))

        script_file = outputs_dir / "threadle_script.txt"
        script_file.write_text(
            "\n".join(
                [
                    "script_nodes = createnodeset(name=script_nodes, createnodes=3)",
                    "script_net = createnetwork(name=script_net, nodeset=script_nodes)",
                    "addlayer(network=script_net, layername=script_layer, mode=1, directed=false, valuetype=binary, selfties=false)",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        show("load threadle script", lambda: th.load_script(str(script_file)))
        show("info script net", lambda: th.info("script_net"))

        delete_me = show("create delete_me", lambda: th.create_nodeset("delete_me", createnodes=1))
        show("delete delete_me", lambda: th.delete(delete_me))
        show("inventory before delete_all", th.i)
        show("delete all", th.delete_all)
        show("inventory after delete_all", th.i)
    finally:
        threadlepy.stop()

    print(f"\nWorkflow complete. Output directory: {outputs_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threadle", default=None, help="Path to the Threadle CLI executable.")
    parser.add_argument("--timeout", type=float, default=1800.0, help="Threadle response timeout in seconds.")
    args = parser.parse_args()
    return run(args.threadle, timeout=args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
