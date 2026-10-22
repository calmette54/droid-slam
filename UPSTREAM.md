# Upstream

This repository packages [DROID-SLAM](https://github.com/princeton-vl/droid-slam)
(Teed & Deng, NeurIPS 2021) with the build, test and release infrastructure of
[BazelStarterTemplate](https://github.com/calmette54/BazelStarterTemplate).
It was created from the template, not as a GitHub fork, so it does not carry
the upstream git history.

| Component | Source | Commit |
|---|---|---|
| DROID-SLAM | <https://github.com/princeton-vl/droid-slam> | `2dfd39f0dcad44012ca7bbb8aa70b55edbfa9c99` (2025-05-04) |
| lietorch | <https://github.com/princeton-vl/lietorch> | `7f687644fcea81ab337831749445224503c1290d` (fetched by Bazel) |
| pytorch_scatter | <https://github.com/rusty1s/pytorch_scatter> | replaced, see below |

The upstream code is licensed under the BSD 3-Clause License (`LICENSE`).

## Imported unchanged

`droid_slam/`, `src/`, `demo.py`, `train.py`, `view_reconstruction.py`,
`evaluation_scripts/`, `tools/*.sh`, `calib/`, `data/euroc_groundtruth/`,
`misc/`, `LICENSE`. The upstream README is in
`documentation/UPSTREAM_README.md`.

These paths are excluded from the formatters and linters so that they stay
diffable against upstream (`.ruff.toml`, `src/.clang-format`, `devenv.nix`).

## Dropped

| Upstream | Replaced by |
|---|---|
| `setup.py` (`droid_backends` CUDAExtension) | `//src:droid_backends` (rules_cuda) |
| `thirdparty/lietorch` submodule | `@lietorch` (`http_archive`) |
| `thirdparty/pytorch_scatter` submodule | `//third_party/torch_scatter` (pure PyTorch `scatter_sum`/`scatter_mean`) |
| `thirdparty/tartanair_tools` | not used by the SLAM system |
| `requirements*.txt`, `environment*.yaml` | `requirements.in` / `requirements_lock.txt` |
| `.gitmodules`, `.gitignore` | Bazel external repositories, template `.gitignore` |

## Deviations

- PyTorch 2.7.0 with **CUDA 12.8** wheels (upstream: CUDA 12.6), because nvcc
  12.8 is the first release that accepts the template's clang 19 as host
  compiler.
- `opencv-python-headless` instead of `opencv-python`.

## Local patches

None yet.
