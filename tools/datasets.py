"""The evaluation datasets of DROID-SLAM, as in the upstream tools/*.sh scripts.

Shared by //tools:download_dataset and //benchmark:accuracy. Paths are relative
to the directory the tools are run from (the repository root upstream).
"""

import dataclasses

EUROC = [
    "MH_01_easy",
    "MH_02_easy",
    "MH_03_medium",
    "MH_04_difficult",
    "MH_05_difficult",
    "V1_01_easy",
    "V1_02_medium",
    "V1_03_difficult",
    "V2_01_easy",
    "V2_02_medium",
    "V2_03_difficult",
]

TUM = [
    "rgbd_dataset_freiburg1_360",
    "rgbd_dataset_freiburg1_desk",
    "rgbd_dataset_freiburg1_desk2",
    "rgbd_dataset_freiburg1_floor",
    "rgbd_dataset_freiburg1_plant",
    "rgbd_dataset_freiburg1_room",
    "rgbd_dataset_freiburg1_rpy",
    "rgbd_dataset_freiburg1_teddy",
    "rgbd_dataset_freiburg1_xyz",
]

# tools/evaluate_eth3d.sh: the training scenes that are not dark.
ETH3D = [
    "cables_1",
    "cables_2",
    "cables_3",
    "camera_shake_1",
    "camera_shake_2",
    "camera_shake_3",
    "ceiling_1",
    "ceiling_2",
    "desk_3",
    "desk_changing_1",
    "einstein_1",
    "einstein_2",
    "einstein_flashlight",
    "einstein_global_light_changes_1",
    "einstein_global_light_changes_2",
    "einstein_global_light_changes_3",
    "kidnap_1",
    "large_loop_1",
    "mannequin_1",
    "mannequin_3",
    "mannequin_4",
    "mannequin_5",
    "mannequin_7",
    "mannequin_face_1",
    "mannequin_face_2",
    "mannequin_face_3",
    "mannequin_head",
    "motion_1",
    "planar_2",
    "planar_3",
    "plant_1",
    "plant_2",
    "plant_3",
    "plant_4",
    "plant_5",
    "plant_scene_1",
    "plant_scene_2",
    "plant_scene_3",
    "reflective_1",
    "repetitive",
    "sfm_bench",
    "sfm_garden",
    "sfm_house_loop",
    "sfm_lab_room_1",
    "sfm_lab_room_2",
    "sofa_1",
    "sofa_2",
    "sofa_3",
    "sofa_4",
    "sofa_shake",
    "table_3",
    "table_4",
    "table_7",
    "vicon_light_1",
    "vicon_light_2",
]

# evaluation_scripts/test_tartanair.py (MONO_TEST_SCENES, STEREO_TEST_SCENES).
TARTANAIR_MONO = [f"M{s}{i:03d}" for s in ["E", "H"] for i in range(8)]
TARTANAIR_STEREO = [f"S{s}{i:03d}" for s in ["E", "H"] for i in range(8)]


@dataclasses.dataclass(frozen=True)
class Archive:
    """One download, extracted into `into` and marked done by `name`."""

    name: str
    url: str = ""
    gdrive_id: str = ""
    into: str = "."
    # A file inside the zip at `url`, fetched alone with HTTP range requests.
    member: str = ""


# EuRoC moved from robotics.ethz.ch/~asl-datasets (upstream's URLs, offline) to
# the ETH Research Collection (doi:10.3929/ethz-b-000690084), one zip per room
# that holds the original per-sequence zips.
_EUROC_ROOMS = {
    "MH": ("machine_hall", "7b2419c1-62b5-4714-b7f8-485e5fe3e5fe"),
    "V1": ("vicon_room1", "02ecda9a-298f-498b-970c-b7c44334d880"),
    "V2": ("vicon_room2", "ea12bc01-3677-4b4c-853d-87c7870b8c44"),
}


def _euroc(seq: str, into: str) -> Archive:
    room, bitstream = _EUROC_ROOMS[seq[:2]]
    return Archive(
        seq,
        f"https://www.research-collection.ethz.ch/server/api/core/bitstreams/{bitstream}/content",
        into=into,
        member=f"{room}/{seq}/{seq}.zip",
    )


@dataclasses.dataclass(frozen=True)
class Dataset:
    root: str
    archives: tuple[Archive, ...]
    # Upstream: "EuRoC and TUM can be run on a 1080Ti. The TartanAir and
    # ETH3D-SLAM datasets will require 24G of memory."
    min_gpu_gb: float


DATASETS = {
    # tools/download_sample_data.sh
    "sample": Dataset(
        root="data",
        archives=(
            Archive(
                "sfm_bench_mono", "https://www.eth3d.net/data/slam/datasets/sfm_bench_mono.zip"
            ),
            Archive(
                "rgbd_dataset_freiburg3_cabinet",
                "https://cvg.cit.tum.de/rgbd/dataset/freiburg3/rgbd_dataset_freiburg3_cabinet.tgz",
            ),
            _euroc("MH_03_medium", into="."),
        ),
        min_gpu_gb=0,
    ),
    "euroc": Dataset(
        root="datasets/EuRoC",
        archives=tuple(_euroc(seq, into=seq) for seq in EUROC),
        min_gpu_gb=11,
    ),
    "tum": Dataset(
        root="datasets/TUM-RGBD",
        archives=tuple(
            Archive(seq, f"https://cvg.cit.tum.de/rgbd/dataset/freiburg1/{seq}.tgz") for seq in TUM
        ),
        min_gpu_gb=11,
    ),
    "eth3d": Dataset(
        root="datasets/ETH3D-SLAM",
        archives=tuple(
            Archive(f"{seq}_{mode}", f"https://www.eth3d.net/data/slam/datasets/{seq}_{mode}.zip")
            for seq in ETH3D
            for mode in ["mono", "rgbd"]
        ),
        min_gpu_gb=24,
    ),
    "tartanair": Dataset(
        root="datasets/tartanair_test",
        archives=(
            Archive("images", gdrive_id="1N8qoU-oEjRKdaKSrHPWA-xsnRtofR_jJ"),
            Archive(
                "groundtruth",
                "https://cmu.box.com/shared/static/3p1sf0eljfwrz4qgbpc6g95xtn2alyfk.zip",
            ),
        ),
        min_gpu_gb=24,
    ),
}
