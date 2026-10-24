# Accuracy on a 6 GB GPU

Results of `//benchmark:accuracy` with the default `--memory auto` on an
NVIDIA GeForce RTX 3060 Laptop GPU (6 GB; about 4.8 GB free next to the
desktop), torch 2.7.0+cu128, run on 2026-10-23. ATE RMSE in meters, against the
DROID-SLAM paper (arXiv 2108.10869v2, `reference.json`). The runs aren't
deterministic, so repeated runs vary slightly.

The low-memory arguments are `--backend_thresh=20 --backend_nms=3`. EuRoC and
ETH3D-SLAM also get `--buffer=384`.

## EuRoC, monocular (Table 3)

All 11 sequences pass `--check`. The mean ATE is 0.023 m; the paper reports 0.022 m.

| Sequence | ATE | Paper |
|---|---|---|
| MH_01_easy | 0.013 | 0.013 |
| MH_02_easy | 0.012 | 0.014 |
| MH_03_medium | 0.022 | 0.022 |
| MH_04_difficult | 0.048 | 0.043 |
| MH_05_difficult | 0.044 | 0.043 |
| V1_01_easy | 0.037 | 0.037 |
| V1_02_medium | 0.012 | 0.012 |
| V1_03_difficult | 0.018 | 0.020 |
| V2_01_easy | 0.020 | 0.017 |
| V2_02_medium | 0.010 | 0.013 |
| V2_03_difficult | 0.015 | 0.014 |

With upstream's `--buffer=512`, the global bundle adjustment of V1_03_difficult
and V2_02_medium runs out of memory. They have about 310 keyframes.

## TUM-RGBD fr1, monocular (Table 4)

All 9 sequences pass `--check`. The mean ATE is 0.029 m; the paper reports 0.038 m.

| Sequence | ATE | Paper |
|---|---|---|
| fr1_360 | 0.070 | 0.111 |
| fr1_desk | 0.016 | 0.018 |
| fr1_desk2 | 0.026 | 0.042 |
| fr1_floor | 0.021 | 0.021 |
| fr1_plant | 0.014 | 0.016 |
| fr1_room | 0.050 | 0.049 |
| fr1_rpy | 0.023 | 0.026 |
| fr1_teddy | 0.034 | 0.048 |
| fr1_xyz | 0.010 | 0.012 |

## ETH3D-SLAM, RGB-D training scenes (Figure 4)

51 of the 55 non-dark training scenes complete. The AUC up to 8 cm is
327.3; the paper reports 340.42 for the training split. A failed scene counts
as 0. The median ATE is 0.006 m, 47 scenes are below 8 cm and 42 below 2 cm.

- **Too large for 6 GB:**
  - desk_changing_1 and reflective_1 have more than 512 keyframes.
  - desk_3 needs more than 384 keyframes and runs out of memory at 512.
  - The global bundle adjustment of camera_shake_2 builds about 5800 edges (4.4 GiB).
- **Lost tracking:** above 0.5 m on `einstein_flashlight`, `einstein_global_light_changes_1`, `einstein_global_light_changes_3` and `kidnap_1`.

Upstream's `--buffer=1024` preallocates about 4 GB of keyframe features, so
without the smaller buffer most scenes run out of memory before tracking.

## TartanAir test, monocular (Table 1)

TartanAir doesn't fit in 6 GB. At 384×512 MH000 has more than 512 keyframes,
and ME000 runs out of memory with a 512 buffer. Upstream asks for 24 GB.
`benchmark:accuracy` skips it on smaller GPUs unless `--force` is given.
