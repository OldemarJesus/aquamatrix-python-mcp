# Release and Publishing

## GitHub Pages setup

The `documentation.yml` workflow builds the MkDocs site for pull requests and deploys it after pushes to `main` or a manual workflow run. In repository settings, choose **Pages → Build and deployment → Source → GitHub Actions**. The site URL is <https://oldemarjesus.github.io/aquamatrix-python-mcp/>.

## PyPI trusted publishing setup

Configure the publisher once:

1. Create the `aquamatrix-simar-mcp` project on PyPI or open its publishing settings.
2. Add a pending trusted publisher with owner `OldemarJesus`, repository `aquamatrix-python-mcp`, workflow filename `publish.yml`, and environment `pypi`.
3. Create a GitHub repository environment named `pypi`. Add protection/approval rules if appropriate.
4. Update `project.version` in `pyproject.toml`, run checks, and commit the release.
5. Create and publish a GitHub Release with a matching version tag, for example `v0.1.0`.

The workflow verifies that the release tag matches the package version, runs tests/lint/type checks, builds the source and wheel distributions, and publishes the validated artifacts using GitHub OIDC. No PyPI API token is stored as a GitHub secret.

PyPI versions are immutable. For a failed or already-published version, fix the issue and release a new version rather than reusing the same one.