# CLAUDE.md

Guidance for Claude Code in this repository: DROID-SLAM (princeton-vl) with hermetic Bazel + CUDA builds.
Python 3.12, built with Bazel (bzlmod) and rules_python.

Bootstrapped from BazelStarterTemplate v3.1.0-1-ga53b253 (see `.bazel-starter.json`).
Infrastructure (build, CI, release, lint, docs, image) follows that template:
use the `bazel-starter` plugin skills (`project-standardize`, `bazel-workspace`,
`devenv-env`) to change it or to upgrade to a newer template release.

## Setup

- Enter the dev environment with `devenv shell` (bazelisk, commitizen, jq,
  crane and the git hooks).
- Once per clone: `bazelisk run @tweag-credential-helper//installer`.
- Always run `bazelisk`, never `bazel`: `.bazeliskrc` selects the Aspect CLI,
  which runs the Bazel version from `.bazelversion`.

## Commands

```bash
bazelisk build //...                          # build everything
bazelisk test //...                           # unit tests, lint tests, integration
bazelisk run //standalone:hello-world -- Alice fr
bazelisk run //:format                        # clang-format and ruff
bazelisk lint //...                           # lint results with fixes
bazelisk run //:requirements.update           # re-lock after editing requirements.in
bazelisk build //documentation:docs           # Doxygen HTML in bazel-bin/documentation/html
```

`//integration:standalone_image_test` needs a Docker-compatible daemon. For
rootless Podman, export `DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock`
and `TESTCONTAINERS_RYUK_DISABLED=true`. See `integration/BUILD.bazel`.

Release builds stamp the version from `.release-please-manifest.json`:

```bash
bazelisk build //standalone:tar --config=x86_64 --revision_mode=RELEASE --release_version=X.Y.Z
bazelisk run //standalone:push_image --revision_mode=RELEASE
```

## Layout

| Path | Contents |
|---|---|
| `lib/greeter/` | example library (`py_library`, `import greeter`) |
| `test/greeter/`, `test/lint/` | pytest unit tests, ruff `lint_test` |
| `requirements.in`, `requirements_lock.txt` | PyPI dependencies (hub `@pypi`) |
| `standalone/` | `hello-world` CLI, release tarball, multi-arch OCI image |
| `integration/` | Python testcontainers test of the image |
| `documentation/` | Doxygen + doxygen-awesome |
| `bzl/` | flags (`defs.bzl`), packaging names, platforms, toolchain, format and lint setup, project parameters (`variables.bzl`) |
| `tools/workspace_status.sh` | stamp keys (version, commit, image registry) |

## Conventions

- Commit with `cz commit` (conventional commits). release-please derives
  versions and the CHANGELOG from them on `main`.
- Code must pass `bazelisk test //...`, including the lint tests in
  `test/lint/` (warnings are errors). Run `bazelisk run //:format` before committing.
- Project-wide values (name, description, repository URL, image name) belong in
  `bzl/variables.bzl`, not in BUILD files.
- Toolchain-wide settings live in `MODULE.bazel`, `bzl/toolchains.MODULE.bazel`
  and `.bazelrc`. Pin every dependency (BCR first; `sha256` on `http_archive`).

## CI/CD

- **GitHub Actions** (`.github/workflows/ci.yml`) builds and tests on pushes
  and PRs with `--config=ci`. The runners have no GPU: tests tagged
  `requires-gpu` or `requires-docker` are skipped there.
- **GitHub Actions** (`.github/workflows/release-please.yml`) runs on `main`:
  it opens the release PR, and when that PR is merged it attaches the
  binaries, pushes the image and publishes the docs to GitHub Pages.

## Tools for Claude

- `.mcp.json` provides **context7** (current library docs) and **grep** (code
  search across GitHub). Use them before guessing an API or a configuration.
- The `bazel-starter` plugin provides the agents `bazel-build-expert`,
  `cicd-automation-architect`, `documentation-architect` and `sprint-planner`.
