#!/usr/bin/env python3
"""Run every wrapper added for Threadle 1.3 against the bundled example data.

Each step calls one wrapper on a real Threadle process; the script reports every
failing step and exits with status 1 if any failed.

Usage:
    python3 scripts/test_threadle_13_commands.py [--threadle PATH]
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import threadlepy
import threadlepy.client as client
import threadlepy.commands as th


def steps(tmp: str):
    lz, my = "lazega", "mynet"
    graphml = os.path.join(tmp, "lazega.graphml")
    attrs = os.path.join(tmp, "attrs.tsv")
    with open(attrs, "w", encoding="utf-8") as f:
        f.write("node\tsenior\n1\t1\n2\t0\n")

    return [
        ("about", lambda: th.about()["ThreadlepyVersion"]),
        ("system_info", lambda: th.system_info()),
        # centrality
        ("betweenness_centrality", lambda: th.betweenness_centrality(lz, "friends")),
        ("closeness_centrality", lambda: th.closeness_centrality(lz, ["friends", "advice"], traversal="both")),
        ("harmonic_centrality", lambda: th.harmonic_centrality(lz, "friends", normalize=False)),
        ("eigenvector_centrality", lambda: th.eigenvector_centrality(lz, "collaboration", traversal="both")),
        ("pagerank", lambda: th.pagerank(lz, "advice", dampingfactor=0.85)),
        ("edge_betweenness_centrality", lambda: th.edge_betweenness_centrality(lz, "collaboration")),
        # cohesion, structural holes, communities
        ("clustering_coefficient", lambda: th.clustering_coefficient(lz, "collaboration", method="wattsstrogatz")),
        ("transitivity", lambda: th.transitivity(lz, "collaboration")),
        ("coreness", lambda: th.coreness(lz, "collaboration")),
        ("constraint", lambda: th.constraint(lz, "collaboration")),
        ("effective_size", lambda: th.effective_size(lz, "collaboration")),
        ("community_detection", lambda: th.community_detection(lz, "collaboration", type="leiden", resolution=1.0)),
        ("small_world_coefficient", lambda: th.small_world_coefficient(lz, "collaboration", nulltrials=3)),
        ("assortativity", lambda: th.assortativity(my, "kinship", "gender")),
        ("degree_assortativity", lambda: th.degree_assortativity(lz, "friends")),
        # census and distances
        ("dyad_census", lambda: th.dyad_census(lz, "friends")),
        ("triadic_census", lambda: th.triadic_census(lz, "friends")),
        ("diameter", lambda: th.diameter(lz, "friends")),
        ("eccentricity", lambda: th.eccentricity(lz, "collaboration")),
        ("shortest_paths", lambda: th.shortest_paths(lz, [1, 2], [3, 4], returnpaths=True)),
        ("shortest_paths_attributes", lambda: th.info(th.shortest_paths_attributes("sp_gender", my, "gender", "kinship"))),
        # layer / network / nodeset operations
        ("duplicate", lambda: th.duplicate(lz, "layer", "friends", "friends_copy")),
        ("rename", lambda: th.rename(lz, "layer", "friends_copy", "friends_renamed")),
        ("binary_to_valued", lambda: th.binary_to_valued(lz, "friends")),
        ("symmetric_to_directed", lambda: th.symmetric_to_directed(lz, "collaboration")),
        ("rewire", lambda: th.rewire(lz, "friends", numswaps=50)),
        ("merge_layers", lambda: th.merge_layers(lz, "friends", "advice", method="or")),
        ("merge_nodesets", lambda: th.info(th.merge_nodesets("ns_merged", "lazega_nodeset", "lazega_female_nodeset"))),
        ("merge_networks", lambda: th.info(th.merge_networks("net_merged", lz, "lazega_female", onvalueconflict="keepfirst"))),
        ("export (graphml)", lambda: th.export(lz, graphml, format="graphml")),
        ("import_network", lambda: th.info(th.import_network("lz_imported", graphml))),
        # attributes and tables
        ("convert_attr", lambda: th.convert_attr(my, "gender", "gender_str", attrtype="string")),
        ("set_attrs (one value)", lambda: th.set_attrs(lz, "flag", nodes=[1, 2, 3], attrvalue=1)),
        ("set_attrs (per node)", lambda: th.set_attrs(lz, "flag", nodes=[1, 2, 3], attrvalues=[4, 5, 6])),
        ("import_node_attributes", lambda: th.import_node_attributes(lz, attrs)),
        ("get_attrs_table", lambda: th.get_attrs_table(lz, nodes=[1, 2, 3], attrnames=["flag", "senior"])),
        ("get_layer_stats", lambda: th.get_layer_stats(my, "trade")),
        ("get_alter_details", lambda: th.get_alter_details(lz, [1, 2], "friends", attrname="flag", cond="ge", attrvalue=5)),
    ]


def run(threadle_path: str | None) -> int:
    path = threadle_path or "threadle"
    if not threadlepy.is_available(path):
        print("SKIP: Threadle CLI was not found.")
        return 0
    client.configure(print_messages=False)
    failures = []
    with tempfile.TemporaryDirectory() as tmp, threadlepy.session(path):
        th.load_examples(["lazega", "lazega_female", "mynet"], assign=False)
        th.define_attr("lazega", "flag", attrtype="int")
        for name, fn in steps(tmp):
            try:
                result = fn()
                print(f"ok    {name}: {str(result)[:100]}")
            except Exception as e:  # report every failing step, not only the first
                failures.append(name)
                print(f"FAIL  {name}: {e}")
    print(f"\n{len(failures)} failed" + (f": {', '.join(failures)}" if failures else ""))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--threadle", help="path to the Threadle executable")
    return run(ap.parse_args().threadle)


if __name__ == "__main__":
    raise SystemExit(main())
