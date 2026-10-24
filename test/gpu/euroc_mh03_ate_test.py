"""EuRoC MH_03_medium (upstream sample data) reaches the paper's ATE.

Needs a GPU and the sample data (`bazelisk run //tools:download_dataset -- sample`):

    DROID_SAMPLE_DIR=$PWD/data bazelisk test --config=gpu //test/gpu:euroc_mh03_ate_test
"""

import json
import os
import pathlib

import torch
from python.runfiles import Runfiles

from benchmark import accuracy

SEQ = "MH_03_medium"


def test_mh03_ate():
    assert os.environ.get("DROID_SAMPLE_DIR"), f"set DROID_SAMPLE_DIR (see {__file__})"
    # download_dataset puts the sample sequence at data/mav0, as upstream does.
    datapath = pathlib.Path(os.environ["DROID_SAMPLE_DIR"])
    assert (datapath / "mav0/cam0/data").is_dir(), f"no EuRoC sequence in {datapath}"

    runfiles = Runfiles.Create()
    suite = accuracy.SUITES["euroc"]
    cmd = [
        runfiles.Rlocation("_main/evaluation_scripts/test_euroc"),
        f"--datapath={datapath}",
        f"--gt={runfiles.Rlocation(f'_main/data/euroc_groundtruth/{SEQ}.txt')}",
        f"--weights={runfiles.Rlocation(os.environ['DROID_DEFAULT_WEIGHTS'])}",
        "--disable_vis",
        # Below upstream's 11 GB, a sparser global BA (see benchmark/accuracy.py).
        *accuracy.memory_args(
            suite, "auto", torch.cuda.get_device_properties(0).total_memory / 2**30
        ),
    ]
    log = pathlib.Path(os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR", os.environ["TEST_TMPDIR"]))
    result = accuracy.run_sequence(suite, SEQ, cmd, log / f"{SEQ}.log")
    print(f"{SEQ}: {result}")

    reference = json.loads(
        pathlib.Path(runfiles.Rlocation("_main/benchmark/reference.json")).read_text()
    )
    assert not accuracy.check("euroc", {SEQ: result}, reference, tolerance=0.25)


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q", "-s"]))
