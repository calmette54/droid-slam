"""lietorch's tests on the CPU."""

import pytest
from lietorch_cases import *  # noqa: F403


@pytest.fixture
def device():
    return "cpu"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
