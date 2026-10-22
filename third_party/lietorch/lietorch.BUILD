# BUILD file for https://github.com/princeton-vl/lietorch (see MODULE.bazel),
# replacing its setup.py. Only `lietorch_backends` is built: DROID-SLAM does
# not use `lietorch_extras`.
load("@//:bzl/torch_extension.bzl", "torch_cuda_extension")
load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:py_library.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

licenses(["notice"])

exports_files(["LICENSE"])

torch_cuda_extension(
    name = "lietorch_backends",
    srcs = [
        "lietorch/src/lietorch.cpp",
        "lietorch/src/lietorch_cpu.cpp",
    ],
    hdrs = glob(["lietorch/include/*.h"]),
    copts = ["-O2"],
    cuda_srcs = ["lietorch/src/lietorch_gpu.cu"],
    includes = ["lietorch/include"],
    deps = ["@eigen"],
)

filegroup(
    name = "python_srcs",
    srcs = glob(
        ["lietorch/*.py"],
        exclude = [
            "lietorch/gradcheck.py",
            "lietorch/run_tests.py",
        ],
    ),
)

# `import lietorch` (lietorch/group_ops.py imports `lietorch_backends`)
py_library(
    name = "lietorch",
    srcs = [":python_srcs"],
    data = [":lietorch_backends.so"],
    imports = ["."],
    deps = [
        requirement("numpy"),
        requirement("torch"),
    ],
)

# lietorch's own tests (`from gradcheck import ...`, `import run_tests`).
py_library(
    name = "run_tests",
    testonly = True,
    srcs = [
        "lietorch/gradcheck.py",
        "lietorch/run_tests.py",
    ],
    imports = ["lietorch"],
    deps = [":lietorch"],
)
