#!/usr/bin/env bash
# This script will be run by bazel when building process starts to
# generate key-value information that represents the status of the
# workspace. The output should be like
#
# KEY1 VALUE1
# KEY2 VALUE2
#
# If the script exits with non-zero code, it's considered as a failure
# and the output will be discarded.
#
set -eo pipefail # exit immediately if any command fails.

function remove_url_credentials() {
  if command -v perl >/dev/null; then
    perl -pe 's#//.*?:.*?@#//#'
  else
    cat
  fi
}

# Empty in a clone without an origin remote (e.g. a freshly created project).
repo_url=$({ git config --get remote.origin.url || true; } | remove_url_credentials)
echo "REPO_URL $repo_url"

# Placeholders before the first commit.
commit_sha=$(git rev-parse --verify -q HEAD || echo 0000000000000000000000000000000000000000)
commit_sha_short=${commit_sha:0:6}
echo "COMMIT_SHA $commit_sha"

# release-please bumps this manifest in every release PR, so it holds the
# version of the current release.
version_tag=$(sed -n 's/.*"\.": *"\([^"]*\)".*/\1/p' .release-please-manifest.json)

# Note: the "STABLE_" suffix causes these to be part of the "stable" workspace
# status, which may trigger rebuilds of certain targets if these values change
# and you're building with the "--stamp" flag.
echo "STABLE_GIT_COMMIT $commit_sha"
echo "STABLE_GIT_COMMIT_SHORT $commit_sha_short"
echo "STABLE_SEMANTIC_VERSION ${version_tag:-0.0.0}"

# Image registry: $IMAGE_REGISTRY if set, otherwise ghcr.io/<repository owner>
# (from GitHub Actions, or parsed from the origin URL). ghcr.io requires
# lowercase names.
repo_owner=${GITHUB_REPOSITORY_OWNER:-$(echo "$repo_url" | sed -E 's#^.*[:/]([^/]+)/[^/]+$#\1#')}
image_registry=${IMAGE_REGISTRY:-ghcr.io/$(echo "$repo_owner" | tr '[:upper:]' '[:lower:]')}
echo "STABLE_IMAGE_REGISTRY $image_registry"
