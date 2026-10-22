"""Linter aspects.

Run them with the Aspect CLI (`bazelisk lint //...`, configured in
.aspect/cli/config.yaml) or with plain Bazel:

    bazelisk build //... --aspects=//bzl/lint:linters.bzl%clang_tidy \
        --output_groups=rules_lint_human
"""

load("@aspect_rules_lint//lint:clang_tidy.bzl", "lint_clang_tidy_aspect")
load("@aspect_rules_lint//lint:lint_test.bzl", "lint_test")
load("@aspect_rules_lint//lint:ruff.bzl", "lint_ruff_aspect")

clang_tidy = lint_clang_tidy_aspect(
    binary = Label("//bzl/lint:clang_tidy"),
    global_config = [Label("//:.clang-tidy")],
    lint_target_headers = True,
    angle_includes_are_system = False,
    verbose = False,
)

clang_tidy_test = lint_test(aspect = clang_tidy)

ruff = lint_ruff_aspect(
    binary = Label("@aspect_rules_lint//format:ruff"),
    configs = [Label("//:.ruff.toml")],
)

ruff_test = lint_test(aspect = ruff)
