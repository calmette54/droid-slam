"""The subset of torch_scatter (rusty1s/pytorch_scatter) used by DROID-SLAM.

`scatter_sum` and `scatter_mean` with torch_scatter's semantics, in plain
PyTorch, so that the pytorch_scatter CUDA extension does not have to be
built: `index` is broadcast to `src` (a 1-D index addresses dimension
`dim`), and the output has `dim_size` (default `index.max() + 1`) entries
along `dim`. Empty bins are 0.
"""

import torch

__all__ = ["scatter_mean", "scatter_sum"]


def _broadcast(index: torch.Tensor, src: torch.Tensor, dim: int) -> torch.Tensor:
    if index.dim() == 1:
        shape = [1] * src.dim()
        shape[dim] = -1
        index = index.view(shape)
    return index.expand_as(src)


def _output_size(src: torch.Tensor, index: torch.Tensor, dim: int, dim_size: int | None):
    size = list(src.size())
    size[dim] = dim_size if dim_size is not None else (int(index.max()) + 1 if index.numel() else 0)
    return size


def scatter_sum(
    src: torch.Tensor,
    index: torch.Tensor,
    dim: int = -1,
    out: torch.Tensor | None = None,
    dim_size: int | None = None,
) -> torch.Tensor:
    """Sums the slices of `src` that have the same `index` along `dim`."""
    dim = dim % src.dim()
    index = _broadcast(index, src, dim)
    if out is None:
        out = src.new_zeros(_output_size(src, index, dim, dim_size))
    return out.scatter_add_(dim, index, src)


def scatter_mean(
    src: torch.Tensor,
    index: torch.Tensor,
    dim: int = -1,
    out: torch.Tensor | None = None,
    dim_size: int | None = None,
) -> torch.Tensor:
    """Averages the slices of `src` that have the same `index` along `dim`."""
    dim = dim % src.dim()
    out = scatter_sum(src, index, dim, out, dim_size)
    count = scatter_sum(torch.ones_like(src), index, dim, None, out.size(dim))
    count = count.clamp(min=1)
    if out.is_floating_point():
        return out / count
    return out.div(count, rounding_mode="floor")


def __getattr__(name: str):
    raise AttributeError(
        f"torch_scatter.{name} is not provided by //third_party/torch_scatter "
        "(only scatter_sum and scatter_mean are used by DROID-SLAM)"
    )
