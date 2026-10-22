"""Prints the PyTorch / CUDA setup seen by Bazel-built Python binaries."""

import torch


def main() -> int:
    cudnn = torch.backends.cudnn.version()
    print(f"torch {torch.__version__} (CUDA {torch.version.cuda}, cuDNN {cudnn})")
    if not torch.cuda.is_available():
        print("CUDA is not available: check the NVIDIA driver (nvidia-smi)")
        return 1
    for i in range(torch.cuda.device_count()):
        major, minor = torch.cuda.get_device_capability(i)
        print(f"cuda:{i} {torch.cuda.get_device_name(i)} (sm_{major}{minor})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
