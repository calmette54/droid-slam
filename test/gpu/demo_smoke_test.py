"""Runs //:demo end to end on a real sequence and checks the reconstruction.

Needs a GPU, the weights and a sequence (see test/gpu/BUILD.bazel):

    DROID_IMAGEDIR=$PWD/data/sfm_bench/rgb \\
        bazelisk test --config=gpu //test/gpu:demo_smoke_test
"""

import os
import pathlib
import subprocess

import torch
from python.runfiles import Runfiles

REQUIRED = ["DROID_IMAGEDIR"]


def test_demo_reconstruction():
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    assert not missing, f"set {', '.join(missing)} (see {__file__})"

    runfiles = Runfiles.Create()
    demo = runfiles.Rlocation("_main/demo")
    calib = runfiles.Rlocation("_main/calib/" + os.environ.get("DROID_CALIB", "eth.txt"))
    weights = os.environ.get("DROID_WEIGHTS") or runfiles.Rlocation(
        os.environ["DROID_DEFAULT_WEIGHTS"]
    )
    out = pathlib.Path(os.environ["TEST_TMPDIR"]) / "reconstruction.pth"

    subprocess.run(
        [
            demo,
            f"--imagedir={os.environ['DROID_IMAGEDIR']}",
            f"--calib={calib}",
            f"--weights={weights}",
            f"--reconstruction_path={out}",
            "--disable_vis",
        ],
        check=True,
    )

    reconstruction = torch.load(out)
    poses = reconstruction["poses"]
    assert len(poses) >= 8, "fewer keyframes than the warmup"
    assert torch.isfinite(poses).all()
    assert torch.isfinite(reconstruction["disps"]).all()


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
