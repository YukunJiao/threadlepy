# Publishing to PyPI

The workflow in `.github/workflows/publish.yml` builds and checks both the source
distribution and wheel on pushes to `main`/`master`, pull requests, and published
GitHub Releases. The same built wheel is tested on Linux, Windows, and macOS with
Python 3.9, 3.12, and 3.14 (nine combinations). macOS uses the Intel runner to
include Python 3.9. Only a published Release uploads the checked distributions
to PyPI. Draft Releases and ordinary commits do not publish a package.

Publishing uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
through GitHub OIDC. No PyPI API token or GitHub secret is needed.

## One-time setup

1. Push the workflow to the repository's default branch.
2. In the GitHub repository, open **Settings → Environments**, and create an
   environment named `pypi`. If you set deployment restrictions, allow the
   release tags (`v*`). Required reviewers are optional; configuring them adds
   a manual approval before each upload.
3. Log into PyPI and open
   [threadlepy → Manage → Publishing](https://pypi.org/manage/project/threadlepy/settings/publishing/).
   Add a GitHub Trusted Publisher with these exact values:

   | Field | Value |
   | --- | --- |
   | Owner | `YukunJiao` |
   | Repository name | `threadlepy` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

   The workflow name is the filename, not the workflow's display name or full path.

## Publish a release

1. Choose an unused PyPI version. Update `version` in `pyproject.toml` and
   `__version__` in `src/threadlepy/__init__.py` to the same value. Update
   `CHANGELOG.md` as appropriate.
2. Commit and push the changes; wait for the package build and API checks to pass.
3. On GitHub, open **Releases → Draft a new release**. Create a tag named
   `v<VERSION>` on that commit (for example, `v0.2.0` for version `0.2.0`),
   add release notes, and click **Publish release**.
4. Follow **Actions → Build and publish Python package**. Its `build` job checks
   the tag and versions, builds the packages, and validates metadata. The `test`
   matrix installs the built wheel on each OS/Python combination and runs
   `python -m unittest discover -s tests -v`. Only after all nine combinations
   pass does `publish` upload those same artifacts to PyPI.

## What the matrix checks

- Installation and imports of the wheel, and agreement between its metadata version
  and `threadlepy.__version__`.
- Presence of the bundled example datasets, example script, and `py.typed` marker.
- Copying example datasets into nested paths containing spaces and Unicode names,
  including preserving or replacing existing files according to `overwrite`.

These are package compatibility checks. They do not launch Threadle or validate
backend algorithms or subprocess communication. The existing integration scripts
in `scripts/` require a working Threadle executable; running them in CI would also
require provisioning the backend for each platform. The separate `api-check`
workflow checks wrapper definitions against the committed API snapshot.

## Version and upload notes

The example version is illustrative: check PyPI before choosing a new version.
The workflow does not increment versions or create Releases automatically.
GitHub prereleases also trigger publication; use a PEP 440 prerelease version
such as `0.2.0rc1` with tag `v0.2.0rc1` for a PyPI prerelease.

PyPI does not allow replacing an uploaded distribution with the same filename.
For a corrected package, increment the version and publish a new Release. If an
upload fails, inspect the logs and PyPI before rerunning it: a partial upload may
have already published some files. Build artifacts are also available from the
workflow run for inspection.
