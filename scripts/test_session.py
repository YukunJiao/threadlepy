#!/usr/bin/env python3
"""Smoke test the context-managed Threadle lifecycle.

This script is intentionally small: it demonstrates the recommended scripting
style with `threadlepy.session()`, loads bundled example data, runs a couple of
queries, and verifies that the process is stopped after leaving the `with`
block.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import threadlepy
import threadlepy.client as client
import threadlepy.commands as th


def run(threadle_path: str | None = None, *, timeout: float = 1800.0) -> int:
    path = threadle_path or "threadle"
    if not threadlepy.is_available(path):
        print(
            "SKIP: Threadle CLI was not found. Install `threadle`, add it to PATH, "
            "or pass --threadle /full/path/to/threadle.",
            file=sys.stderr,
        )
        return 77

    with threadlepy.session(threadle_path, timeout=timeout, print_messages=False):
        examples = th.load_examples("mynet")
        mynet = examples["mynet"]
        print("info:", th.info(mynet)["Name"])
        print("nodes:", th.get_nbr_nodes(mynet))
        print("density:", th.density(mynet, "kinship"))

    stopped = client.proc is None or client.proc.poll() is not None
    print("session stopped:", stopped)
    if not stopped:
        raise RuntimeError("Threadle process is still running after session exit.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threadle", default=None, help="Path to the Threadle CLI executable.")
    parser.add_argument("--timeout", type=float, default=1800.0, help="Threadle response timeout in seconds.")
    args = parser.parse_args()
    return run(args.threadle, timeout=args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
