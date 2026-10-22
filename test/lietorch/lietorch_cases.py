"""lietorch's own tests (lietorch/run_tests.py), parametrized for pytest."""

import pytest
import run_tests
import torch
from lietorch import SE3, SO3, RxSO3, Sim3

GROUPS = [SO3, RxSO3, SE3, Sim3]

FORWARD = ["test_exp_log", "test_inv", "test_adj", "test_act"]
BACKWARD = [
    "test_adj_grad",
    "test_adjT_grad",
    "test_act_grad",
    "test_matrix_grad",
    "extract_translation_grad",
    "test_vec_grad",
    "test_fromvec_grad",
]
BACKWARD_TOL = ["test_exp_log_grad", "test_inv_log_grad"]


def ids(group):
    return group.__name__


@pytest.fixture(autouse=True)
def seed():
    torch.manual_seed(0)


@pytest.mark.parametrize("group", GROUPS, ids=ids)
@pytest.mark.parametrize("name", FORWARD + BACKWARD)
def test_group(name, group, device):
    getattr(run_tests, name)(group, device=device)


@pytest.mark.parametrize("group", GROUPS, ids=ids)
@pytest.mark.parametrize("name", BACKWARD_TOL)
def test_group_tol(name, group, device):
    # Tolerances of run_tests.py's __main__.
    tol = 1e-3 if group is Sim3 else 1e-8
    getattr(run_tests, name)(group, device=device, tol=tol)
