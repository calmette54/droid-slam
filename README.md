# droid-slam

DROID-SLAM (princeton-vl) with hermetic Bazel + CUDA builds.

## Getting started

Install [Nix](https://nixos.org/download) and [devenv](https://devenv.sh), then:

```bash
devenv shell                                   # every tool the project needs
bazelisk run @tweag-credential-helper//installer   # once per clone
bazelisk test //...
bazelisk run //standalone:hello-world -- Alice fr
```

## Development

- `bazelisk run //:format` formats the code; `bazelisk lint //...` shows lint
  findings with fixes. The lint tests in `test/lint/` fail on any finding.
- Commit with `cz commit` ([Conventional Commits](https://www.conventionalcommits.org)).
  Releases, version numbers and the CHANGELOG are generated from them by
  [release-please](https://github.com/googleapis/release-please).
- Python dependencies: edit `requirements.in`, then `bazelisk run //:requirements.update`.
- API documentation: `bazelisk build //documentation:docs` (published to GitHub
  Pages on every release).

Created from [BazelStarterTemplate](https://github.com/calmette54/BazelStarterTemplate) v3.1.0-1-ga53b253.
