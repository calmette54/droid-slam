"""The DROID-SLAM modules import and the network builds on the CPU."""

import importlib

import pytest
import torch

MODULES = [
    "data_readers.factory",
    "depth_video",
    "droid",
    "droid_async",
    "droid_net",
    "factor_graph",
    "geom.ba",
    "geom.losses",
    "geom.projective_ops",
    "modules.corr",
    "trajectory_filler",
    "visualization",
]


@pytest.mark.parametrize("name", MODULES)
def test_import(name):
    importlib.import_module(name)


def test_droid_net_parameters():
    from droid_net import DroidNet

    net = DroidNet()
    # Matches the keys of the released droid.pth (without the "module." prefix).
    names = {name.split(".")[0] for name, _ in net.named_parameters()}
    assert names == {"fnet", "cnet", "update"}
    assert sum(p.numel() for p in net.parameters()) > 1_000_000


def test_feature_encoder_cpu():
    from droid_net import DroidNet

    net = DroidNet().eval()
    images = torch.rand(1, 2, 3, 64, 96) * 255
    with torch.no_grad():
        fmaps, net_, inp = net.extract_features(images)
    assert fmaps.shape == (1, 2, 128, 8, 12)
    assert net_.shape == inp.shape == (1, 2, 128, 8, 12)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
