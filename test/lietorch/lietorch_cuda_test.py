"""lietorch's tests on the CUDA."""

import pytest
from lietorch_cases import *  # noqa: F403


@pytest.fixture
def device():
    return "cuda"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
