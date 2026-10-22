"""The droid_backends CUDA kernels against the PyTorch code of upstream."""

import pytest
import torch
from lietorch import SE3
from modules.corr import AltCorrBlock, CorrBlock

import droid_backends

DEVICE = "cuda"


@pytest.fixture(autouse=True)
def seed():
    torch.manual_seed(0)


def random_poses(n):
    xi = 0.1 * torch.randn(n, 6, device=DEVICE, dtype=torch.float64)
    # lietorch's LieGroup.float() takes an unused `device` argument.
    return SE3(SE3.exp(xi).data.float())


def test_corr_index_matches_alt_corr():
    # CorrBlock (corr_index_forward on the all-pairs volume) and AltCorrBlock
    # (altcorr_forward, computed on the fly) are interchangeable upstream.
    B, N, C, H, W = 1, 3, 128, 24, 32
    fmaps = torch.randn(B, N, C, H, W, device=DEVICE)
    ii = torch.tensor([0, 1, 2, 0], device=DEVICE)
    jj = torch.tensor([1, 2, 0, 2], device=DEVICE)
    y, x = torch.meshgrid(
        torch.arange(H, device=DEVICE, dtype=torch.float),
        torch.arange(W, device=DEVICE, dtype=torch.float),
        indexing="ij",
    )
    coords = torch.stack([x, y], dim=-1)[None, None].repeat(B, len(ii), 1, 1, 1)
    coords = coords + torch.randn_like(coords)

    dense = CorrBlock(fmaps[:, ii], fmaps[:, jj])(coords)
    alt = AltCorrBlock(fmaps)(coords, ii, jj)
    torch.testing.assert_close(alt, dense, atol=1e-3, rtol=1e-3)


def test_iproj_matches_pinhole_model():
    N, H, W = 2, 6, 8
    fx, fy, cx, cy = 300.0, 310.0, 4.0, 3.0
    intrinsics = torch.tensor([fx, fy, cx, cy], device=DEVICE)
    disps = 0.5 + torch.rand(N, H, W, device=DEVICE)
    poses = random_poses(N)  # camera to world, as passed by visualization.py

    points = droid_backends.iproj(poses.data.contiguous(), disps, intrinsics)

    y, x = torch.meshgrid(
        torch.arange(H, device=DEVICE, dtype=torch.float),
        torch.arange(W, device=DEVICE, dtype=torch.float),
        indexing="ij",
    )
    cam = torch.stack([(x - cx) / fx, (y - cy) / fy, torch.ones_like(x)], dim=-1)
    cam = cam[None] / disps[..., None]
    world = poses[:, None, None] * cam
    torch.testing.assert_close(points.view(N, H, W, 3), world, atol=1e-4, rtol=1e-4)


def test_frame_distance_is_zero_on_the_diagonal():
    N, H, W = 3, 12, 16
    intrinsics = torch.tensor([[300.0, 300.0, 8.0, 6.0]], device=DEVICE).repeat(N, 1)
    disps = 0.5 + torch.rand(N, H, W, device=DEVICE)
    poses = random_poses(N).data.contiguous()
    ii = torch.arange(N, device=DEVICE)

    same = droid_backends.frame_distance(poses, disps, intrinsics[0], ii, ii, 0.3)
    torch.testing.assert_close(same, torch.zeros_like(same), atol=1e-4, rtol=0)

    jj = (ii + 1) % N
    other = droid_backends.frame_distance(poses, disps, intrinsics[0], ii, jj, 0.3)
    assert torch.all(other > 0)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
