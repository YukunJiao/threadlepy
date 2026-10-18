"""Check the installed distribution without requiring the Threadle executable.

Run after installing a built wheel: python -m unittest discover -s tests -v
"""

from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
import tempfile
import unittest

import threadlepy
import threadlepy.commands as commands


class InstalledPackageTests(unittest.TestCase):
    def test_installed_version_matches_public_version(self):
        self.assertEqual(threadlepy.__version__, version("threadlepy"))

    def test_bundled_resources_are_present(self):
        root = files("threadlepy")
        expected = (
            "py.typed",
            "Examples/dscw.tsv",
            "Examples/dscw_nodeset.tsv",
            "Examples/lazega.tsv",
            "Examples/lazega_female.tsv",
            "Examples/lazega_female_nodeset.tsv",
            "Examples/lazega_nodes.tsv",
            "Examples/mynet.tsv",
            "Examples/mynet_nodesetfile.tsv",
            "Examples/mynodes.tsv",
            "Examples/Scripts/create.txt",
        )
        for name in expected:
            with self.subTest(resource=name):
                resource = root.joinpath(name)
                self.assertTrue(resource.is_file(), name)
                if name != "py.typed":
                    self.assertTrue(resource.read_bytes(), name)

    def test_stage_examples_handles_paths_and_overwrite(self):
        # Spaces and non-ASCII names exercise real filesystem operations on each OS.
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "example data 中文" / "nested folder"
            result = commands.stage_examples_to_wd(str(destination))
            self.assertTrue(Path(result).is_absolute())
            self.assertEqual(Path(result).resolve(), destination.resolve())
            resources = files("threadlepy").joinpath("Examples")
            examples = [item for item in resources.iterdir() if item.is_file()]
            self.assertTrue(examples)
            for example in examples:
                with self.subTest(example=example.name):
                    self.assertEqual(
                        (destination / example.name).read_bytes(), example.read_bytes()
                    )

            target = destination / "lazega.tsv"
            target.write_bytes(b"local changes")
            commands.stage_examples_to_wd(str(destination), overwrite=False)
            self.assertEqual(target.read_bytes(), b"local changes")
            commands.stage_examples_to_wd(str(destination), overwrite=True)
            self.assertEqual(target.read_bytes(), resources.joinpath("lazega.tsv").read_bytes())


if __name__ == "__main__":
    unittest.main()
