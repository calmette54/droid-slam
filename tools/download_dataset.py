"""Downloads and extracts the DROID-SLAM evaluation datasets (tools/download_*.sh).

bazelisk run //tools:download_dataset -- sample          # -> data/
bazelisk run //tools:download_dataset -- euroc tum       # -> datasets/EuRoC, ...
bazelisk run //tools:download_dataset -- euroc --only MH_03_medium

Downloads resume after an interruption. A finished archive leaves a
`.<name>.done` marker in the dataset directory and is skipped on the next run.
"""

import argparse
import http.client
import os
import pathlib
import shutil
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile

from tools import datasets

# Some dataset servers close the connection on Python's default User-Agent.
USER_AGENT = "Wget/1.21 (droid-slam download_dataset)"
RETRIES = 5


def fetch_once(url: str, out: pathlib.Path) -> None:
    """Downloads url to out, resuming a partial file."""
    done = out.stat().st_size if out.exists() else 0
    headers = {"User-Agent": USER_AGENT} | ({"Range": f"bytes={done}-"} if done else {})
    try:
        # Fixed http(s) dataset URLs from tools/datasets.py.
        response = urllib.request.urlopen(urllib.request.Request(url, headers=headers))  # noqa: S310
    except urllib.error.HTTPError as error:
        if error.code == 416:  # the partial file is already complete
            return
        raise
    with response:
        mode = "ab" if response.status == 206 else "wb"
        written = done if mode == "ab" else 0
        total = int(response.headers.get("Content-Length", 0)) + written
        with out.open(mode) as f:
            while chunk := response.read(1 << 20):
                f.write(chunk)
                written += len(chunk)
                if total:
                    print(f"\r  {written >> 20} / {total >> 20} MiB", end="", flush=True)
    print()
    if total and written != total:
        raise ConnectionError(f"{url}: got {written} of {total} bytes")


def fetch(url: str, out: pathlib.Path) -> None:
    for attempt in range(1, RETRIES + 1):
        try:
            fetch_once(url, out)
            return
        except (
            ConnectionError,
            TimeoutError,
            http.client.HTTPException,
            urllib.error.URLError,
        ) as error:
            if attempt == RETRIES:
                raise
            print(f"  {error}; retrying ({attempt}/{RETRIES - 1})")
            time.sleep(2**attempt)


def extract(archive: pathlib.Path, into: pathlib.Path) -> None:
    into.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            z.extractall(into)
    else:
        with tarfile.open(archive) as t:
            t.extractall(into, filter="data")


def download(archive: datasets.Archive, root: pathlib.Path) -> None:
    marker = root / f".{archive.name}.done"
    if marker.exists():
        print(f"{archive.name}: already downloaded")
        return
    root.mkdir(parents=True, exist_ok=True)
    part = root / f".{archive.name}.part"
    print(f"{archive.name}: downloading")
    if archive.gdrive_id:
        import gdown  # noqa: PLC0415 (only TartanAir is on Google Drive)

        gdown.download(id=archive.gdrive_id, output=str(part), quiet=False, resume=True)
    else:
        fetch(archive.url, part)
    print(f"{archive.name}: extracting")
    extract(part, root / archive.into)
    part.unlink()
    marker.touch()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset", nargs="+", choices=sorted(datasets.DATASETS))
    parser.add_argument(
        "--only", nargs="+", metavar="NAME", help="only these archives (sequence names)"
    )
    args = parser.parse_args()

    # `bazelisk run` starts in the runfiles tree; resolve against the caller's cwd.
    cwd = pathlib.Path(os.environ.get("BUILD_WORKING_DIRECTORY", "."))
    for name in args.dataset:
        dataset = datasets.DATASETS[name]
        archives = [
            a
            for a in dataset.archives
            if not args.only or any(a.name.startswith(o) for o in args.only)
        ]
        if not archives:
            print(f"{name}: nothing matches --only {' '.join(args.only)}", file=sys.stderr)
            return 1
        root = cwd / dataset.root
        for archive in archives:
            download(archive, root)
        print(f"{name}: {root} ({shutil.disk_usage(root).free >> 30} GiB free)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
