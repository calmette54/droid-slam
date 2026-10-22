"""Downloads the pretrained DROID-SLAM weights (tools/download_model.sh).

bazelisk run //tools:download_model            # -> ./droid.pth
bazelisk run //tools:download_model -- OUT.pth
"""

import argparse
import hashlib
import os
import pathlib

import gdown

GDRIVE_ID = "1PpqVt1H4maBa_GbPJp4NwxRsd9jk-elh"
SHA256 = "46476ef64cde45a97504910d6f3de2eef7b398ec1c6e4e668815c29076024526"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", nargs="?", default="droid.pth")
    args = parser.parse_args()

    # `bazelisk run` starts in the runfiles tree; resolve against the caller's cwd.
    out = pathlib.Path(os.environ.get("BUILD_WORKING_DIRECTORY", ".")) / args.out
    if out.is_file() and sha256(out) == SHA256:
        print(f"{out} is up to date")
        return 0
    gdown.download(id=GDRIVE_ID, output=str(out), quiet=False)
    if sha256(out) != SHA256:
        print(f"{out}: unexpected SHA-256 (expected {SHA256})")
        return 1
    print(f"Saved {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
