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
./tools/download_sample_data.sh                # data/
droid-run //:demo --imagedir=data/sfm_bench/rgb --calib=calib/eth.txt
```

`droid-run` is `bazelisk run` from the current directory, so the upstream
command lines work as documented (`demo.py`, `train.py`,
`view_reconstruction.py` are `//:demo`, `//:train`, `//:view_reconstruction`;
`evaluation_scripts/test_*.py` are `//evaluation_scripts:test_*`).
The visualizer needs a display; use `--disable_vis` on a headless machine.

Or with the container image (NVIDIA container toolkit):

```bash
bazelisk run //standalone:load_host_image      # droid-slam:integration-test
docker run --rm --gpus all -v "$PWD:/work" droid-slam:integration-test \
    --imagedir=/work/data/sfm_bench/rgb --calib=calib/eth.txt \
    --weights=/work/droid.pth --disable_vis
```

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
