"""DROID-SLAM's CUDA kernels (the module upstream's setup.py builds).

The extension links against the shared libraries of the torch wheel, so
torch is imported (and its libraries loaded) first.
"""

import torch  # noqa: F401  (loads libtorch*.so)

from _droid_backends import *  # noqa: F403
