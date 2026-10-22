"""PyTorch C++/CUDA extensions, the Bazel version of torch.utils.cpp_extension."""

load("@rules_cc//cc:cc_binary.bzl", "cc_binary")
load("@rules_cc//cc:cc_library.bzl", "cc_library")
load("@rules_cuda//cuda:defs.bzl", "cuda_library")

# torch._C._PYBIND11_*: the pybind11 ABI tag must match the one of the
# torch wheel, otherwise torch's pybind11 types are not shared with the
# extension (checked by //test/extensions:import_test).
_PYBIND11_DEFINES = [
    'PYBIND11_COMPILER_TYPE=\\"_gcc\\"',
    'PYBIND11_STDLIB=\\"_libstdcpp\\"',
    'PYBIND11_BUILD_ABI=\\"_cxxabi1016\\"',
]

# Flags of CUDAExtension (torch.utils.cpp_extension.COMMON_NVCC_FLAGS).
_NVCC_COPTS = [
    "-D__CUDA_NO_HALF_OPERATORS__",
    "-D__CUDA_NO_HALF_CONVERSIONS__",
    "-D__CUDA_NO_BFLOAT16_CONVERSIONS__",
    "-D__CUDA_NO_HALF2_OPERATORS__",
    "--expt-relaxed-constexpr",
    "-std=c++17",
]

_TORCH = Label("//third_party/torch")
_PYTHON_HEADERS = Label("@rules_python//python/cc:current_py_cc_headers")
_CUDA_HEADERS = Label("@cuda//:cuda_headers")

def torch_cuda_extension(
        name,
        srcs,
        cuda_srcs = [],
        hdrs = [],
        includes = [],
        copts = [],
        deps = [],
        **kwargs):
    """Builds `<name>.so`, a Python extension module named `name`.

    Args:
      name: name of the Python module (TORCH_EXTENSION_NAME).
      srcs: C++ sources (the pybind11 bindings).
      cuda_srcs: CUDA sources.
      hdrs: private headers of srcs and cuda_srcs.
      includes: include directories of hdrs, relative to the package.
      copts: extra compiler flags for both C++ and CUDA (e.g. "-O3").
      deps: cc_library deps (e.g. Eigen).
      **kwargs: common attributes (visibility, tags, ...).
    """
    defines = [
        "TORCH_EXTENSION_NAME=" + name,
        "TORCH_API_INCLUDE_EXTENSION_H",
    ] + _PYBIND11_DEFINES
    compatible = ["@platforms//os:linux", "@platforms//cpu:x86_64"]
    common = {
        "target_compatible_with": compatible,
        "tags": kwargs.pop("tags", []),
    }
    visibility = kwargs.pop("visibility", None)

    cc_srcs = [name + "_cc"]
    cc_library(
        name = name + "_cc",
        srcs = srcs + hdrs,
        copts = ["-std=c++17", "-fvisibility=hidden"] + copts,
        includes = includes,
        local_defines = defines,
        deps = deps + [_TORCH, _PYTHON_HEADERS, _CUDA_HEADERS],
        alwayslink = True,
        **common
    )
    if cuda_srcs:
        cuda_library(
            name = name + "_cuda",
            srcs = cuda_srcs,
            hdrs = hdrs,
            copts = _NVCC_COPTS + copts,
            host_copts = ["-fPIC"],
            includes = includes,
            local_defines = defines,
            deps = deps + [_TORCH, _PYTHON_HEADERS],
            alwayslink = True,
            **common
        )
        cc_srcs.append(name + "_cuda")

    cc_binary(
        name = name + ".so",
        linkshared = True,
        deps = cc_srcs,
        visibility = visibility,
        **common
    )
