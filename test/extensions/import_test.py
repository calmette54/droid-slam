"""The Bazel-built CUDA extensions import on a machine without a GPU."""

import pathlib

import pytest
import torch

import _droid_backends
import droid_backends

DROID_BACKENDS = [
    "altcorr_backward",
    "altcorr_forward",
    "ba",
    "corr_index_backward",
    "corr_index_forward",
    "depth_filter",
    "frame_distance",
    "iproj",
    "projmap",
]


@pytest.mark.parametrize("name", DROID_BACKENDS)
def test_droid_backends_exports(name):
    assert callable(getattr(droid_backends, name))


def test_cxx11_abi_matches_torch():
    assert torch._C._GLIBCXX_USE_CXX11_ABI


def test_pybind11_abi_matches_torch():
    # The pybind11 ABI tag (bzl/torch_extension.bzl) must be the one of the
    # torch wheel, or the extension gets its own pybind11 internals.
    binary = pathlib.Path(_droid_backends.__file__).read_bytes()
    for tag in (
        torch._C._PYBIND11_COMPILER_TYPE,
        torch._C._PYBIND11_STDLIB,
        torch._C._PYBIND11_BUILD_ABI,
    ):
        assert tag.encode() in binary, tag


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
