# droid-slam

[DROID-SLAM](https://github.com/princeton-vl/droid-slam) (Teed & Deng,
NeurIPS 2021) with hermetic Bazel builds: the CUDA extensions are compiled by
Bazel (CUDA 12.8 from NVIDIA's redistributables, PyTorch 2.7.0+cu128 from the
locked wheels), so the only system requirement is the NVIDIA driver.

The SLAM code is upstream's, unchanged (see [UPSTREAM.md](UPSTREAM.md) for
the commits and the few deviations); the infrastructure comes from
[BazelStarterTemplate](https://github.com/calmette54/BazelStarterTemplate)
v3.1.0-1-ga53b253. The upstream README is in
[documentation/UPSTREAM_README.md](documentation/UPSTREAM_README.md).

## Getting started

Install [Nix](https://nixos.org/download), [devenv](https://devenv.sh) and an
NVIDIA driver for CUDA 12.8 (>= 570), then:

```bash
devenv shell                                   # every tool the project needs
bazelisk run @tweag-credential-helper//installer   # once per clone
gpu-check                                      # driver, PyTorch, CUDA, GPUs
bazelisk test //...                            # CPU tests
bazelisk test --config=gpu //...               # GPU tests
```

Run the demo on the upstream sample data:

```bash
bazelisk run //tools:download_model            # droid.pth
bazelisk run //tools:download_dataset -- sample  # data/
droid-run //:demo --imagedir=data/sfm_bench/rgb --calib=calib/eth.txt
```

`droid-run` is `bazelisk run` from the current directory, so the upstream
command lines work as documented (`demo.py`, `train.py`,
`view_reconstruction.py` are `//:demo`, `//:train`, `//:view_reconstruction`;
`evaluation_scripts/test_*.py` are `//evaluation_scripts:test_*`).
The visualizer needs a display and the system OpenGL library (`libGL.so.1`,
Ubuntu package `libgl1`), which open3d loads on import; use `--disable_vis`
on a headless machine.

The weights are the authors' `droid.pth`, loaded unchanged at run time: Bazel
compiles only the CUDA operators, and the network is the upstream Python code.
Besides the Google Drive original (`//tools:download_model`), the same file
(SHA-256 `46476ef6…6024526`) is mirrored in the
[`weights-v1`](https://github.com/calmette54/droid-slam/releases/tag/weights-v1)
release, which Bazel fetches as `@droid_weights//file` for the tests.

Or with the container image (NVIDIA container toolkit):

```bash
bazelisk run //standalone:load_host_image      # droid-slam:integration-test
docker run --rm --gpus all -v "$PWD:/work" droid-slam:integration-test \
    --imagedir=/work/data/sfm_bench/rgb --calib=calib/eth.txt \
    --weights=/work/droid.pth --disable_vis
```

## Accuracy benchmark

The upstream evaluation (TartanAir, EuRoC, TUM-RGBD and ETH3D-SLAM) runs with
`//benchmark:accuracy`. It calls the upstream `evaluation_scripts/test_*.py`
once per sequence, with the arguments of `tools/evaluate_*.sh`. It writes the
ATE per sequence to `results/benchmark/<suite>.json` and compares it with the
paper (`benchmark/reference.json`):

```bash
bazelisk run //tools:download_dataset -- euroc tum   # datasets/
bazelisk run //benchmark:accuracy -- euroc --check   # also euroc_stereo, tum, eth3d, tartanair[_stereo]
bazelisk run //benchmark:accuracy -- euroc --only MH_01_easy MH_03_medium
DROID_SAMPLE_DIR=$PWD/data bazelisk test --config=gpu //test/gpu:euroc_mh03_ate_test
```

Upstream says EuRoC and TUM-RGBD fit an 11 GB GPU, while TartanAir and
ETH3D-SLAM need 24 GB. Below 11 GB, the runs use a sparser global bundle
adjustment (`--backend_thresh=20 --backend_nms=3`, `--memory=low`; force either
way with `--memory`). Its per-edge state is what overflows smaller GPUs. EuRoC
and ETH3D also get a smaller preallocated keyframe buffer (`--buffer=384`
instead of 512 or 1024). With these settings EuRoC, TUM-RGBD and ETH3D run on
an RTX 3060 Laptop GPU (6 GB); see `benchmark/RESULTS.md`. TartanAir doesn't fit
in 6 GB and is skipped on smaller GPUs unless `--force` is given. Arguments after the second `--` go to every run, and the
JSON records all extra arguments (`run_args`). `--check` allows 25% plus 1 cm
over the paper per sequence.

## Layout

| Path | Contents |
|---|---|
| `droid_slam/`, `src/`, `demo.py`, ... | upstream DROID-SLAM (`//droid_slam`, `//src:droid_backends`) |
| `third_party/lietorch/` | BUILD file for `@lietorch` (`lietorch_backends`) |
| `third_party/torch_scatter/` | `scatter_sum` / `scatter_mean` in plain PyTorch |
| `third_party/torch/`, `bzl/torch*.bzl` | the torch wheel's C++ API, `torch_cuda_extension` |
| `test/` | CPU tests, GPU tests (`requires-gpu`), lint |
| `standalone/`, `integration/` | release tarball, OCI image and its test |

## Development

- `bazelisk run //:format` formats the code; `bazelisk lint //...` shows lint
  findings with fixes. The lint tests in `test/lint/` fail on any finding.
  The upstream code is excluded from both (see `UPSTREAM.md`).
- Commit with `cz commit` ([Conventional Commits](https://www.conventionalcommits.org)).
  Releases, version numbers and the CHANGELOG are generated from them by
  [release-please](https://github.com/googleapis/release-please).
- Python dependencies: edit `requirements.in`, then run `lock-requirements`.
- API documentation: `bazelisk build //documentation:docs` (published to GitHub
  Pages on every release).

## License

DROID-SLAM and lietorch: BSD 3-Clause, Princeton Vision & Learning Lab
([LICENSE](LICENSE)). tartanair_tools: BSD 3-Clause, Carnegie Mellon
University.
