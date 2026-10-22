# droid-slam

[DROID-SLAM](https://github.com/princeton-vl/droid-slam) (Teed & Deng,
NeurIPS 2021) built with Bazel: the CUDA kernels of `droid_backends` and
`lietorch_backends` are compiled by a hermetic CUDA 12.8 toolchain against
the PyTorch 2.7.0+cu128 wheel. Generated with [Doxygen](https://www.doxygen.nl/)
and the [Doxygen Awesome](https://github.com/jothepro/doxygen-awesome-css) theme:

```bash
bazelisk build //documentation:docs   # output: bazel-bin/documentation/html
```

## Pages

- `UPSTREAM_README.md`: the upstream README (paper, demos, evaluation).
- `src/droid.cpp`: the Python bindings of `droid_backends` (bundle
  adjustment, correlation lookup, depth filtering).
- `src/droid_kernels.cu`: dense bundle adjustment (Schur complement on the
  GPU, Eigen sparse Cholesky for the pose system).
- `src/correlation_kernels.cu`, `src/altcorr_kernel.cu`: correlation volume
  lookup, precomputed and on the fly.
- `torch_scatter`: the pure PyTorch `scatter_sum` / `scatter_mean`.

## Build graph

<pre class="mermaid">
graph TD;
    demo["//:demo"]-->droid_slam["//droid_slam"];
    droid_slam-->droid_backends["//src:droid_backends"];
    droid_slam-->lietorch["@lietorch"];
    droid_slam-->torch_scatter["//third_party/torch_scatter"];
    droid_backends-->torch["//third_party/torch (torch wheel)"];
    lietorch-->torch;
    droid_backends-->cuda["@cuda (rules_cuda, CUDA 12.8)"];
    lietorch-->cuda;
</pre>
