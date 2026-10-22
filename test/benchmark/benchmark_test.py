"""//tools:download_dataset and //benchmark:accuracy without a GPU or the datasets."""

import functools
import http.server
import io
import pathlib
import tarfile
import threading
import zipfile

import pytest

from benchmark import accuracy
from tools import datasets, download_dataset

# The tail of an evo APE result, as printed by evaluation_scripts/test_*.py.
EVO_OUTPUT = """\
APE w.r.t. translation part (m)
(with Sim(3) Umeyama alignment)

       max	0.051300
      mean	0.019212
    median	0.017734
       min	0.002361
      rmse	0.021884
       sse	0.778437
       std	0.009281
"""


def test_datasets_match_upstream_scripts():
    assert len(datasets.EUROC) == 11
    assert len(datasets.TUM) == 9
    # 63 lines in tools/evaluate_eth3d.sh, minus the 8 commented-out dark scenes.
    assert len(datasets.ETH3D) == 55
    assert not any("dark" in s for s in datasets.ETH3D)
    assert datasets.TARTANAIR_MONO[0] == "ME000" and datasets.TARTANAIR_MONO[-1] == "MH007"
    assert set(accuracy.SUITES) >= {"euroc", "tum", "eth3d", "tartanair"}


def test_parse_evo_rmse():
    assert accuracy.EVO_RMSE.findall(EVO_OUTPUT) == ["0.021884"]


def test_parse_tartanair():
    out = "Results\nMH004: 0.0123\n[0.0123]\nMean ATE 0.0123\n"
    assert accuracy.SUITES["tartanair"].pattern("MH004").findall(out) == ["0.0123"]


def test_check_against_paper():
    reference = {"euroc": {"ate": {"MH_01_easy": 0.013, "MH_02_easy": 0.014}}}
    results = {
        "MH_01_easy": {"ate": 0.020, "log": "a.log"},  # within 25% + 1 cm
        "MH_02_easy": {"ate": 0.100, "log": "b.log"},
    }
    problems = accuracy.check("euroc", results, reference, tolerance=0.25)
    assert len(problems) == 1 and problems[0].startswith("MH_02_easy")
    results["MH_01_easy"]["ate"] = None
    assert len(accuracy.check("euroc", results, reference, tolerance=0.25)) == 2


def _archives(tmp_path: pathlib.Path) -> pathlib.Path:
    served = tmp_path / "served"
    served.mkdir()
    with zipfile.ZipFile(served / "seq.zip", "w") as z:
        z.writestr("mav0/cam0/data/0.png", b"x" * 4096)
    with tarfile.open(served / "seq.tgz", "w:gz") as t:
        data = b"y" * 4096
        info = tarfile.TarInfo("rgbd_seq/rgb/0.png")
        info.size = len(data)
        t.addfile(info, io.BytesIO(data))
    return served


@pytest.fixture
def server(tmp_path):
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(_archives(tmp_path))
    )
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_download_and_extract(server, tmp_path):
    root = tmp_path / "datasets"
    download_dataset.download(datasets.Archive("seq", f"{server}/seq.zip", into="seq"), root)
    download_dataset.download(datasets.Archive("tum", f"{server}/seq.tgz"), root)
    assert (root / "seq/mav0/cam0/data/0.png").read_bytes() == b"x" * 4096
    assert (root / "rgbd_seq/rgb/0.png").read_bytes() == b"y" * 4096
    assert (root / ".seq.done").exists() and not (root / ".seq.part").exists()

    # Done archives are skipped, even if the server no longer has them.
    download_dataset.download(datasets.Archive("seq", f"{server}/gone.zip"), root)


def test_fetch_resumes(server, tmp_path):
    full = (tmp_path / "served" / "seq.zip").read_bytes()
    part = tmp_path / "seq.part"
    part.write_bytes(full[:100])
    download_dataset.fetch(f"{server}/seq.zip", part)
    assert part.read_bytes() == full


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
