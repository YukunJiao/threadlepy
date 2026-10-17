#!/usr/bin/env python3
"""Exercise threadlepy's public command wrappers against bundled example data.

This is an integration smoke test, modeled after the threadleR vignette. It
requires a working Threadle CLI executable. By default the script searches for
`threadle` on PATH; pass --threadle /full/path/to/threadle when needed.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import threadlepy
import threadlepy.commands as th


Step = tuple[str, Callable[[], Any]]


def _print_result(label: str, value: Any) -> None:
    if value is None:
        print(f"  OK {label}")
        return
    text = repr(value)
    if len(text) > 180:
        text = text[:177] + "..."
    print(f"  OK {label}: {text}")


def _run_steps(title: str, steps: list[Step]) -> None:
    print(f"\n== {title} ==")
    for label, fn in steps:
        _print_result(label, fn())


def run(threadle_path: str | None = None, *, timeout: float = 1800.0) -> int:
    path = threadle_path or "threadle"
    if not threadlepy.is_available(path):
        print(
            "SKIP: Threadle CLI was not found. Install `threadle`, add it to PATH, "
            "or pass --threadle /full/path/to/threadle.",
            file=sys.stderr,
        )
        return 77

    threadlepy.configure(print_messages=False, timeout=timeout)
    threadlepy.start(threadle_path)

    try:
        _run_steps(
            "public surface",
            [
                ("threadleR aliases present", lambda: all(hasattr(th, name) for name in ("th_i", "th_info", "th_load_examples", "th_shortest_path", "th_rwfpt"))),
                ("stage examples", lambda: th.stage_examples_to_wd(str(Path(tempfile.gettempdir()) / "threadlepy_examples_smoke"))),
                ("sync wd", th.sync_wd),
                ("setting verbose off", lambda: th.setting("verbose", False)),
            ],
        )

        _run_steps(
            "load bundled examples",
            [
                ("load mynet", lambda: th.load_examples("mynet")),
                ("inventory", th.i),
                ("workdir", th.get_workdir),
                ("dir", th.dir),
                ("mynet info", lambda: th.info("mynet")),
                ("mynet nodeset info", lambda: th.info("mynet_nodeset")),
                ("preview mynet", lambda: th.preview("mynet")),
            ],
        )

        _run_steps(
            "nodes and attributes",
            [
                ("node count", lambda: th.get_nbr_nodes("mynet")),
                ("all nodes", lambda: th.get_all_nodes("mynet", offset=0, limit=8)),
                ("node by index", lambda: th.get_nodeid_by_index("mynet", index=0)),
                ("random node", lambda: th.get_random_node("mynet")),
                ("single attr", lambda: th.get_attr("mynet_nodeset", 123, "gender")),
                ("batch attrs", lambda: th.get_attrs("mynet_nodeset", [123, 234, 345], "gender")),
                ("attr summary", lambda: th.get_attr_summary("mynet_nodeset", "gender")),
            ],
        )

        _run_steps(
            "one-mode layers",
            [
                ("get edge", lambda: th.get_edge("mynet", "trade", 123, 345)),
                ("check edge", lambda: th.check_edge("mynet", "kinship", 123, 345)),
                ("all edges", lambda: th.get_all_edges("mynet", "trade", offset=0, limit=10)),
                ("random edge", lambda: th.get_random_edge("mynet", "trade")),
                ("alters", lambda: th.get_node_alters("mynet", 345, layernames="trade", direction="both")),
                ("degree lookup", lambda: th.get_degree("mynet", 345, layernames="trade", direction="both")),
                ("random alter", lambda: th.get_random_alter("mynet", 345, layernames="trade", direction="both")),
                ("density", lambda: th.density("mynet", "kinship")),
                ("components", lambda: th.components("mynet", "kinship", attrname="kinship_component_py")),
                ("degree attr", lambda: th.degree("mynet", "kinship", attrname="kinship_degree_py", direction="both")),
                ("shortest path", lambda: th.shortest_path("mynet", 123, 567, layernames="kinship")),
                (
                    "shortest paths for pairs",
                    lambda: th.shortest_paths("mynet", [123, 567], [567, 123], layernames="kinship", returnpaths=True),
                ),
                (
                    "shortest paths by gender",
                    lambda: th.shortest_paths_attributes("paths_by_gender_py", "mynet", "gender", layernames="kinship"),
                ),
            ],
        )

        _run_steps(
            "two-mode layers",
            [
                ("all hyperedges", lambda: th.get_all_hyperedges("mynet", "work", offset=0, limit=10)),
                ("hyperedge nodes", lambda: th.get_hyperedge_nodes("mynet", "work", "ias")),
                ("node hyperedges", lambda: th.get_node_hyperedges("mynet", "work", 123)),
                ("add hyper", lambda: th.add_hyper("mynet", "work", "py_temp", nodes=[123, 234])),
                ("add affiliation", lambda: th.add_aff("mynet", "work", 345, "py_temp")),
                ("remove affiliation", lambda: th.remove_aff("mynet", "work", 345, "py_temp")),
                ("remove hyper", lambda: th.remove_hyper("mynet", "work", "py_temp")),
                ("project two-mode", lambda: th.project_two_mode("mynet", "work", method="count", newlayername="work_projected_py")),
            ],
        )

        _run_steps(
            "derived structures and transforms",
            [
                (
                    "filter nodeset",
                    lambda: th.filter("female_nodeset_py", "mynet_nodeset", "gender", "eq", "f"),
                ),
                ("subnet", lambda: th.subnet("female_mynet_py", "mynet", "female_nodeset_py")),
                ("symmetrize", lambda: th.symmetrize("mynet", "trade", method="max", newlayername="trade_sym_py")),
                (
                    "dichotomize",
                    lambda: th.dichotomize(
                        "mynet",
                        "trade",
                        cond="ge",
                        threshold=1000,
                        truevalue=1,
                        falsevalue=0,
                        newlayername="trade_hi_py",
                    ),
                ),
                ("pack", lambda: th.pack("mynet", "kinship")),
                ("unpack", lambda: th.unpack("mynet", "kinship")),
            ],
        )

        _run_steps(
            "scratch editing",
            [
                ("create nodeset", lambda: th.create_nodeset("scratch_nodes_py", name="Scratch nodes", createnodes=5)),
                ("create network", lambda: th.create_network("scratch_net_py", "scratch_nodes_py", name="Scratch network")),
                ("add layer", lambda: th.add_layer("scratch_net_py", "friendship", mode=1, directed=False)),
                ("add edge", lambda: th.add_edge("scratch_net_py", "friendship", 1, 2)),
                ("remove edge", lambda: th.remove_edge("scratch_net_py", "friendship", 1, 2)),
                ("clear layer", lambda: th.clear_layer("scratch_net_py", "friendship")),
                ("remove layer", lambda: th.remove_layer("scratch_net_py", "friendship")),
                ("add node", lambda: th.add_node("scratch_nodes_py", 10)),
                ("remove node", lambda: th.remove_node("scratch_nodes_py", 10)),
                ("define attr", lambda: th.define_attr("scratch_nodes_py", "score", "int")),
                ("set attr", lambda: th.set_attr("scratch_nodes_py", 1, "score", 7)),
                ("remove attr", lambda: th.remove_attr("scratch_nodes_py", 1, "score")),
                ("undefine attr", lambda: th.undefine_attr("scratch_nodes_py", "score")),
                ("generate attr", lambda: th.generate_attr("scratch_nodes_py", "rand_score", "int", min=1, max=10)),
                ("random seed", lambda: th.random_seed(42)),
                ("add er layer", lambda: th.add_layer("scratch_net_py", "er", mode=1, directed=False)),
                ("generate er", lambda: th.generate("scratch_net_py", "er", type="er", p=0.25)),
            ],
        )

        with tempfile.TemporaryDirectory(prefix="threadlepy_test_") as tmp:
            tmpdir = Path(tmp)
            exported = tmpdir / "kinship.tsv"
            imported = tmpdir / "imported.tsv"
            saved = tmpdir / "scratch_nodes.tsv"
            gexf = tmpdir / "trade_sym.gexf"
            script = tmpdir / "mini_create.txt"
            imported.write_text("1\t2\t4\n2\t3\t5\n", encoding="utf-8")
            script.write_text(
                "mini_script_nodes = createnodeset(name=mini_script_nodes, createnodes=2)\n",
                encoding="utf-8",
            )

            _run_steps(
                "file IO",
                [
                    ("export layer", lambda: th.export_layer("mynet", "kinship", str(exported), header=True)),
                    ("export gexf", lambda: th.export("mynet", format="gexf", file=str(gexf), layername="trade_sym_py")),
                    ("save file", lambda: th.save_file("scratch_nodes_py", str(saved))),
                    ("load saved nodeset", lambda: th.load_file("scratch_nodes_copy_py", str(saved), type="nodeset")),
                    ("load script", lambda: th.load_script(str(script))),
                    (
                        "add imported layer",
                        lambda: th.add_layer("scratch_net_py", "imported_edges", mode=1, directed=False, valuetype="valued"),
                    ),
                    (
                        "import layer",
                        lambda: th.import_layer(
                            "scratch_net_py",
                            "imported_edges",
                            str(imported),
                            format="edgelist",
                            node1col=0,
                            node2col=1,
                            valuecol=2,
                            header=False,
                            addmissingnodes=True,
                        ),
                    ),
                    ("raw cmd", lambda: th.cmd("info", args={"structure": "mynet"})),
                ],
            )

        _run_steps(
            "cleanup",
            [
                ("delete scratch network", lambda: th.delete("scratch_net_py")),
                ("delete scratch nodes", lambda: th.delete("scratch_nodes_py")),
                ("delete all remaining structures", th.delete_all),
                ("inventory after cleanup", th.i),
            ],
        )

    finally:
        threadlepy.stop()

    print("\nAll command smoke tests completed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threadle", default=None, help="Path to the Threadle CLI executable.")
    parser.add_argument("--timeout", type=float, default=1800.0, help="Threadle response timeout in seconds.")
    args = parser.parse_args()
    return run(args.threadle, timeout=args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
