"""//third_party/torch_scatter against a loop reference."""

import pytest
import torch
from torch_scatter import scatter_mean, scatter_sum


def reference(src, index, dim, dim_size, mean):
    """Loop over the bins of a 1-D index."""
    src = src.movedim(dim, 0)
    out = src.new_zeros((dim_size, *src.shape[1:]))
    for i in range(dim_size):
        selected = src[index == i]
        if len(selected):
            out[i] = selected.mean(0) if mean else selected.sum(0)
    return out.movedim(0, dim)


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
@pytest.mark.parametrize("dim", [0, 1, -1])
@pytest.mark.parametrize("mean", [False, True])
def test_matches_reference(dtype, dim, mean):
    torch.manual_seed(0)
    src = torch.randn(5, 6, 7, dtype=dtype)
    n = src.shape[dim]
    index = torch.randint(0, n - 1, (n,))
    dim_size = n + 2  # empty bins at the end
    scatter = scatter_mean if mean else scatter_sum
    got = scatter(src, index, dim=dim, dim_size=dim_size)
    torch.testing.assert_close(got, reference(src, index, dim, dim_size, mean))


def test_default_dim_size():
    src = torch.ones(4, 3)
    index = torch.tensor([0, 2, 2, 0])
    assert scatter_sum(src, index, dim=0).shape == (3, 3)
    torch.testing.assert_close(scatter_mean(src, index, dim=0)[1], torch.zeros(3))


def test_droid_ba_usage():
    # droid_slam/geom/ba.py: scatter_sum(A[:, v], ii[v] * m + jj[v], dim=1, dim_size=n * m)
    A = torch.randn(1, 5, 6, 6, dtype=torch.float64)
    ii = torch.tensor([0, 1, 1, 2, 0])
    got = scatter_sum(A, ii, dim=1, dim_size=4)
    torch.testing.assert_close(got, reference(A, ii, 1, 4, mean=False))


@pytest.mark.parametrize("scatter", [scatter_sum, scatter_mean])
def test_gradcheck(scatter):
    src = torch.randn(3, 4, 2, dtype=torch.float64, requires_grad=True)
    index = torch.tensor([1, 0, 1, 3])
    assert torch.autograd.gradcheck(lambda x: scatter(x, index, dim=1, dim_size=5), (src,))


def test_unsupported_function():
    import torch_scatter

    with pytest.raises(AttributeError, match="scatter_max"):
        _ = torch_scatter.scatter_max


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
