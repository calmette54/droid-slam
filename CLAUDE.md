# CLAUDE.md

Guidance for Claude Code in this repository: DROID-SLAM (princeton-vl) with hermetic Bazel + CUDA builds.
Python 3.12, built with Bazel (bzlmod) and rules_python.

Bootstrapped from BazelStarterTemplate v3.1.0-1-ga53b253 (see `.bazel-starter.json`).
Infrastructure (build, CI, release, lint, docs, image) follows that template:
use the `bazel-starter` plugin skills (`project-standardize`, `bazel-workspace`,
`devenv-env`) to change it or to upgrade to a newer template release.

## Setup

- Enter the dev environment with `devenv shell` (bazelisk, uv, commitizen,
  jq, crane, wget and the git hooks; scripts `droid-run`, `gpu-check`,
  `lock-requirements`). The NVIDIA driver is the only host dependency.
- Once per clone: `bazelisk run @tweag-credential-helper//installer`.
- Always run `bazelisk`, never `bazel`: `.bazeliskrc` selects the Aspect CLI,
  which runs the Bazel version from `.bazelversion`.

## Commands

```bash
bazelisk build //...                          # build everything (no GPU needed)
bazelisk test //...                           # CPU unit tests and lint tests
bazelisk test --config=gpu //...              # tests tagged requires-gpu
bazelisk run //tools:cuda_check               # PyTorch / CUDA / GPU report
droid-run //:demo --imagedir=... --calib=calib/eth.txt   # run from the cwd
bazelisk run //:format                        # clang-format and ruff
bazelisk lint //...                           # lint results with fixes
lock-requirements                             # re-lock after editing requirements.in
bazelisk build //documentation:docs           # Doxygen HTML in bazel-bin/documentation/html
```

`//integration:standalone_image_test` (manual, ~9 GB image) needs a
Docker-compatible daemon. For
rootless Podman, export `DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock`
and `TESTCONTAINERS_RYUK_DISABLED=true`. See `integration/BUILD.bazel`.

Release builds stamp the version from `.release-please-manifest.json`:

```bash
bazelisk build //standalone:tar --config=release --config=x86_64 --revision_mode=RELEASE --release_version=X.Y.Z
bazelisk run --config=release //standalone:push_image --revision_mode=RELEASE
```

## Layout

| Path | Contents |
|---|---|
| `droid_slam/`, `src/`, `demo.py`, `train.py`, `view_reconstruction.py`, `evaluation_scripts/`, `tools/*.sh`, `calib/`, `data/` | upstream DROID-SLAM, unchanged (`UPSTREAM.md`) |
| `src/BUILD.bazel` | `droid_backends` CUDA extension (`//src:droid_backends`) |
| `third_party/lietorch/` | BUILD file for `@lietorch` (`http_archive`) |
| `third_party/torch_scatter/` | pure PyTorch `scatter_sum` / `scatter_mean` |
| `third_party/tartanair_tools/` | upstream's vendored TartanAir evaluation |
| `third_party/torch/`, `bzl/torch.bzl`, `bzl/torch_extension.bzl` | C++ API of the torch wheel, `torch_cuda_extension` macro |
| `test/` | `extensions`, `lietorch`, `torch_scatter`, `droid_slam` (CPU); `gpu`, `cuda`, `lietorch:lietorch_cuda_test` (`requires-gpu`); `lint` |
| `tools/` | `cuda_check`, `download_model` (weights also as `@droid_weights//file`, release `weights-v1`) |
| `requirements.in`, `requirements_lock.txt` | PyPI + PyTorch cu128 dependencies (hub `@pypi`, uv lock) |
| `standalone/` | release tarball, OCI image (`/demo` entrypoint) |
| `integration/` | Python testcontainers test of the image |
| `documentation/` | Doxygen + doxygen-awesome, upstream README |
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

- Do not reformat or lint the upstream code: it is excluded in `.ruff.toml`,
  `src/.clang-format` and `devenv.nix` so that it stays diffable. Record any
  change to it in `UPSTREAM.md` ("Local patches").
- New Python files: add their targets to `//test/lint:ruff_test`. Tests that
  need a GPU get the `requires-gpu` tag; never skip a test at run time.

## Deviations from the template

Keep these when upgrading with `project-standardize`:

- No BuildBuddy RBE (`WORKSPACE.bzlmod`, `buildbuddy.yaml`, `--enable_workspace`
  removed); CI is `.github/workflows/ci.yml` on GitHub-hosted runners.
- x86_64 only (CUDA redistributables, PyTorch CUDA wheels): no aarch64 image
  or tarball.
- CUDA: rules_cuda 0.3.0 (hermetic 12.8 redist) with nvcc and the LLVM
  toolchain as host compiler; rules_cc 0.2.14; `--config=gpu`,
  `--config=release` (CUDA archs) in `.bazelrc`.
- `bzl/toolchains.MODULE.bazel`: x86_64 links libstdc++ dynamically
  (`dynamic-stdc++`), as the torch wheel does.
- Python dependencies are locked with uv (`lock-requirements`), not
  `compile_pip_requirements`, because of the PyTorch index.
- The release tarball has no runfiles (the runtime exceeds GitHub's 2 GB
  asset limit); the image and the image test are `manual`.

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
