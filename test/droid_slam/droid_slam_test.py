"""The DROID-SLAM modules import and the network builds on the CPU."""

import functools
import importlib
import os

import pytest
import torch
from python.runfiles import Runfiles

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


def test_load_released_weights(monkeypatch):
    """droid.pth loads through upstream's own Droid.load_weights (CPU, strict keys)."""
    import droid
    from droid_net import DroidNet

    # droid.pth holds CUDA tensors and load_weights ends with .to("cuda:0"): stay on
    # the CPU. torch.load keeps its default weights_only=True (torch >= 2.6).
    monkeypatch.setattr(torch, "load", functools.partial(torch.load, map_location="cpu"))
    monkeypatch.setattr(DroidNet, "to", lambda self, *args, **kwargs: self)
    weights = Runfiles.Create().Rlocation(os.environ["DROID_WEIGHTS"])

    stub = type("Stub", (), {})()
    droid.Droid.load_weights(stub, weights)

    # The update block predicts 2 channels for the flow delta and its weight.
    assert stub.net.update.delta[2].out_channels == 2
    assert stub.net.update.weight[2].out_channels == 2
    assert all(torch.isfinite(p).all() for p in stub.net.parameters())


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
