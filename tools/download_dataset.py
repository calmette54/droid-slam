"""Downloads and extracts the DROID-SLAM evaluation datasets (tools/download_*.sh).

bazelisk run //tools:download_dataset -- sample          # -> data/
bazelisk run //tools:download_dataset -- euroc tum       # -> datasets/EuRoC, ...
bazelisk run //tools:download_dataset -- euroc --only MH_03_medium

Downloads resume after an interruption. A finished archive leaves a
`.<name>.done` marker in the dataset directory and is skipped on the next run.
"""

import argparse
import http.client
import io
import os
import pathlib
import shutil
import struct
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
import zlib

from tools import datasets

# Some dataset servers close the connection on Python's default User-Agent.
USER_AGENT = "Wget/1.21 (droid-slam download_dataset)"
RETRIES = 5
# Too Many Requests, Service Unavailable: wait and try again.
RATE_LIMITED = (429, 503)


def _request(url: str, first: int | None = None, last: int | None = None):
    headers = {"User-Agent": USER_AGENT}
    if first is not None:
        headers["Range"] = f"bytes={first}-{'' if last is None else last}"
    for attempt in range(1, RETRIES + 1):
        try:
            # Fixed http(s) dataset URLs from tools/datasets.py.
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers))  # noqa: S310
        except urllib.error.HTTPError as error:
            # The ETH Research Collection rate-limits bursts of range requests.
            if error.code not in RATE_LIMITED or attempt == RETRIES:
                raise
            retry_after = error.headers.get("Retry-After", "")
            wait = int(retry_after) if retry_after.isdigit() else 30 * attempt
            print(f"  HTTP {error.code}; retrying in {wait} s ({attempt}/{RETRIES - 1})")
            time.sleep(wait)
    raise AssertionError("unreachable")


def fetch_once(url: str, out: pathlib.Path, start: int = 0, length: int | None = None) -> None:
    """Downloads url (or `length` bytes from `start`) to out, resuming a partial file."""
    done = out.stat().st_size if out.exists() else 0
    windowed = start or length is not None
    if length is not None and done >= length:
        return
    last = None if length is None else start + length - 1
    try:
        response = _request(url, start + done, last) if done or windowed else _request(url)
    except urllib.error.HTTPError as error:
        if error.code == 416:  # the partial file is already complete
            return
        raise
    with response:
        mode = "ab" if response.status == 206 else "wb"
        if windowed and response.status != 206:
            raise ConnectionError(f"{url}: the server ignores range requests")
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


def fetch(url: str, out: pathlib.Path, start: int = 0, length: int | None = None) -> None:
    for attempt in range(1, RETRIES + 1):
        try:
            fetch_once(url, out, start, length)
            return
        except (
            ConnectionError,
            TimeoutError,
            http.client.HTTPException,
            urllib.error.URLError,
        ) as error:
            if attempt == RETRIES:
                raise
            # The ETH3D server refuses TLS handshakes for a while after a burst.
            wait = 15 * 2**attempt
            print(f"  {error}; retrying in {wait} s ({attempt}/{RETRIES - 1})")
            time.sleep(wait)


class RemoteFile(io.RawIOBase):
    """A read-only, seekable view of a URL through HTTP range requests."""

    def __init__(self, url: str) -> None:
        with _request(url, 0, 0) as response:
            self.size = int(response.headers["Content-Range"].rpartition("/")[2])
            self.url = response.url
        self.pos = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        self.pos = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.size}[whence] + offset
        return self.pos

    def read(self, size: int = -1) -> bytes:
        size = self.size - self.pos if size < 0 else min(size, self.size - self.pos)
        if size <= 0:
            return b""
        with _request(self.url, self.pos, self.pos + size - 1) as response:
            data = response.read()
        self.pos += len(data)
        return data


def fetch_member(url: str, member: str, out: pathlib.Path) -> None:
    """Downloads one deflated or stored file of the remote zip at url to out."""
    remote = RemoteFile(url)
    info = zipfile.ZipFile(remote).getinfo(member)
    remote.seek(info.header_offset)
    header = remote.read(30)  # the local file header, then its name and extra field
    name_length, extra_length = struct.unpack("<HH", header[26:30])
    start = info.header_offset + 30 + name_length + extra_length

    raw = out.with_suffix(".raw")
    fetch(remote.url, raw, start, info.compress_size)
    try:
        crc = inflate_to(raw, out, deflated=info.compress_type == zipfile.ZIP_DEFLATED)
    except zlib.error:
        crc = None
    raw.unlink()
    if crc != info.CRC:
        out.unlink()
        raise ValueError(f"{member}: CRC-32 mismatch, downloaded data removed")


def inflate_to(raw: pathlib.Path, out: pathlib.Path, deflated: bool) -> int:
    """Writes the (raw deflate) data of raw to out and returns its CRC-32."""
    crc = 0
    inflate = zlib.decompressobj(-zlib.MAX_WBITS) if deflated else None
    with raw.open("rb") as src, out.open("wb") as dst:
        while chunk := src.read(1 << 20):
            data = inflate.decompress(chunk) if inflate else chunk
            crc = zlib.crc32(data, crc)
            dst.write(data)
        if inflate:
            data = inflate.flush()
            crc = zlib.crc32(data, crc)
            dst.write(data)
    return crc


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
    elif archive.member:
        fetch_member(archive.url, archive.member, part)
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
