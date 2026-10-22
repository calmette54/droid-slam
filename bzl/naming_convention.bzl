"""Rule to name packages."""

load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain")
load("@rules_pkg//pkg:providers.bzl", "PackageVariablesInfo")
load("@bazel_skylib//rules:common_settings.bzl", "BuildSettingInfo")

def _naming_convention_impl(ctx):
    values = {}

    # Copy attributes from the rule to the provider
    values["product_name"] = ctx.attr.product_name
    values["version"] = ctx.attr._version[BuildSettingInfo].value
    values["commit_sha"] = ctx.attr._commit_sha[BuildSettingInfo].value

    # TODO(https://github.com/bazelbuild/bazel/issues/7260): Switch from
    # calling find_cc_toolchain to direct lookup via the name.
    # cc_toolchain = ctx.toolchains["@rules_cc//cc:toolchain_type"]
    cc_toolchain = find_cc_toolchain(ctx)

    values["target_gnu_system"] = cc_toolchain.target_gnu_system_name
    values["compilation_mode"] = ctx.var.get("COMPILATION_MODE")

    return PackageVariablesInfo(values = values)

#
# A rule to inject variables from the build file into package names.
#
# Extracting variables from the toolchain to use in the package name.
#
naming_convention = rule(
    implementation = _naming_convention_impl,
    # Going forward, the preferred way to depend on a toolchain through the
    # toolchains attribute. The current C++ toolchains, however, are still not
    # using toolchain resolution, so we have to depend on the toolchain
    # directly.
    # TODO(https://github.com/bazelbuild/bazel/issues/7260): Delete the
    # _cc_toolchain attribute.
    attrs = {
        "product_name": attr.string(
            doc = "Placeholder for our final product name.",
        ),
        "_commit_sha": attr.label(
            doc = "Placeholder for the current commit-sha.",
            default = ":commit_sha",
        ),
        "_version": attr.label(
            doc = "Placeholder for our release semantic version.",
            default = ":release_version",
        ),
        "_cc_toolchain": attr.label(
            default = Label(
                "@rules_cc//cc:current_cc_toolchain",
            ),
        ),
    },
    toolchains = ["@rules_cc//cc:toolchain_type"],
    incompatible_use_toolchain_transition = True,
)
