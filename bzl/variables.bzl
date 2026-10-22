"""Shared variables for the entire project.

These are the values to change when creating a new project from this template.
"""

# Name of the product, used for release tarballs, image labels and the docs.
PROJECT_NAME = "droid-slam"

# One-line description, shown in the generated documentation.
PROJECT_DESCRIPTION = "DROID-SLAM (princeton-vl) with hermetic Bazel + CUDA builds"

# Source repository, linked from the generated documentation.
REPOSITORY_URL = "https://github.com/calmette54/droid-slam"

# Name of the container image; the registry comes from tools/workspace_status.sh.
IMAGE_NAME = "droid-slam"

# The DROID-SLAM sources this repository was imported from (see UPSTREAM.md).
UPSTREAM_REPOSITORY = "https://github.com/princeton-vl/droid-slam"
UPSTREAM_COMMIT = "2dfd39f0dcad44012ca7bbb8aa70b55edbfa9c99"
