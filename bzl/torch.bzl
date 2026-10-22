"""C++ API of the PyTorch wheel from the pip hub, for building extensions."""

load("@rules_cc//cc/common:cc_common.bzl", "cc_common")
load("@rules_cc//cc/common:cc_info.bzl", "CcInfo")

_INCLUDE = "/site-packages/torch/include/"
_LIB = "/site-packages/torch/lib/"

def _torch_cc_library_impl(ctx):
    files = ctx.attr.torch[DefaultInfo].default_runfiles.files.to_list()
    headers = [f for f in files if _INCLUDE in f.path]
    if not headers:
        fail("{} has no torch/include/ files".format(ctx.attr.torch.label))
    include = headers[0].path[:headers[0].path.index(_INCLUDE) + len(_INCLUDE) - 1]

    wanted = {"lib{}.so".format(name): True for name in ctx.attr.libs}
    libs = [f for f in files if _LIB in f.path and f.basename in wanted]
    if len(libs) != len(wanted):
        fail("missing torch libraries: {}".format(
            sorted([n for n in wanted if n not in [f.basename for f in libs]]),
        ))

    compilation_context = cc_common.create_compilation_context(
        headers = depset(headers),
        system_includes = depset([include, include + "/torch/csrc/api/include"]),
        defines = depset(["_GLIBCXX_USE_CXX11_ABI=1"]),
    )

    # Link by path: the extension gets DT_NEEDED entries with the libraries'
    # sonames (libtorch.so, ...), which resolve at run time to the copies that
    # `import torch` has already loaded. Nothing is added to the runfiles.
    linker_input = cc_common.create_linker_input(
        owner = ctx.label,
        user_link_flags = depset(["-Wl,--no-as-needed"] + [f.path for f in libs] + ["-Wl,--as-needed"]),
        additional_inputs = depset(libs),
    )
    return [CcInfo(
        compilation_context = compilation_context,
        linking_context = cc_common.create_linking_context(
            linker_inputs = depset([linker_input]),
        ),
    )]

torch_cc_library = rule(
    implementation = _torch_cc_library_impl,
    doc = "Headers and shared libraries of the PyTorch wheel `torch` as a CcInfo.",
    attrs = {
        "libs": attr.string_list(
            doc = "Libraries in torch/lib/ to link, without `lib` and `.so`.",
            mandatory = True,
        ),
        "torch": attr.label(
            doc = "The py_library of the torch wheel (its data holds include/ and lib/).",
            mandatory = True,
        ),
    },
    provides = [CcInfo],
)
