"""Runs the upstream evaluation scripts over a dataset and compares the ATE with the paper.

bazelisk run //benchmark:accuracy -- euroc                  # all 11 sequences
bazelisk run //benchmark:accuracy -- euroc --only MH_03_medium
bazelisk run //benchmark:accuracy -- tum --check            # fail on a regression
bazelisk run //benchmark:accuracy -- euroc_stereo -- --buffer=256

Each sequence runs //evaluation_scripts:test_* in its own process with the
arguments of the upstream tools/evaluate_*.sh, so the numbers are the ones
upstream's scripts print. Logs and results/benchmark/<suite>.json are written
under the current directory; the datasets are expected where
//tools:download_dataset puts them. Arguments after `--` go to every run.
"""

import argparse
import dataclasses
import json
import os
import pathlib
import re
import subprocess
import sys
import time

import numpy as np
import torch
from python.runfiles import Runfiles

from tools import datasets

# A sparser global bundle adjustment (upstream: --backend_thresh=24 or 22,
# --backend_nms=2 or 3) for GPUs below upstream's 11 GB. Its per-edge state
# (up to 16 edges per keyframe) is what runs out of memory on a 6 GB GPU. On
# EuRoC MH_03 with an RTX 3060 (6 GB) it gives ATE 0.0220 m (paper: 0.022).
LOW_MEMORY_ARGS = ["--backend_thresh=20", "--backend_nms=3"]
# Upstream: "EuRoC and TUM can be run on a 1080Ti" (11 GB).
LOW_MEMORY_GB = 11

# evo's APE statistics, as matched by evaluation_scripts/parse_results.py.
EVO_RMSE = re.compile(r"^\s*rmse\s+([0-9]+\.[0-9]+)", re.MULTILINE)


@dataclasses.dataclass(frozen=True)
class Suite:
    dataset: str
    script: str
    sequences: list[str]
    # The arguments of one run for a sequence of the dataset root.
    args: object
    # The result line of the script.
    pattern: object = EVO_RMSE


def _tartanair(stereo: bool) -> Suite:
    mode = "stereo" if stereo else "mono"
    return Suite(
        dataset="tartanair",
        script="test_tartanair",
        sequences=datasets.TARTANAIR_STEREO if stereo else datasets.TARTANAIR_MONO,
        args=lambda root, seq, _: [
            f"--datapath={root / mode}",
            f"--gt_path={root / (mode + '_gt')}",
            f"--scene={seq}",
            *(["--stereo"] if stereo else []),
        ],
        pattern=lambda seq: re.compile(rf"^{seq}: ([0-9.eE+-]+)$", re.MULTILINE),
    )


def _euroc(stereo: bool) -> Suite:
    return Suite(
        dataset="euroc",
        script="test_euroc",
        sequences=datasets.EUROC,
        args=lambda root, seq, runfiles: [
            f"--datapath={root / seq}",
            f"--gt={runfiles.Rlocation(f'_main/data/euroc_groundtruth/{seq}.txt')}",
            *(["--stereo"] if stereo else []),
        ],
    )


SUITES = {
    "euroc": _euroc(stereo=False),
    "euroc_stereo": _euroc(stereo=True),
    "tum": Suite(
        dataset="tum",
        script="test_tum",
        sequences=datasets.TUM,
        args=lambda root, seq, _: [f"--datapath={root / seq}"],
    ),
    "eth3d": Suite(
        dataset="eth3d",
        script="test_eth3d",
        sequences=datasets.ETH3D,
        args=lambda root, seq, _: [f"--datapath={root / seq}"],
    ),
    "tartanair": _tartanair(stereo=False),
    "tartanair_stereo": _tartanair(stereo=True),
}


def memory_args(memory: str, gpu_gb: float) -> list[str]:
    """The extra arguments of --memory (auto: low below upstream's 11 GB)."""
    low = memory == "low" or (memory == "auto" and gpu_gb < LOW_MEMORY_GB)
    return LOW_MEMORY_ARGS if low else []


def run_sequence(suite: Suite, seq: str, cmd: list[str], log: pathlib.Path) -> dict:
    start = time.monotonic()
    # Fewer out-of-memory errors from fragmentation on small GPUs.
    env = {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"} | os.environ
    with log.open("w") as f:
        process = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=f, text=True, cwd=log.parent, env=env, check=False
        )
    seconds = time.monotonic() - start
    with log.open("a") as f:
        f.write(process.stdout)
    pattern = suite.pattern(seq) if callable(suite.pattern) else suite.pattern
    matches = pattern.findall(process.stdout)
    ate = float(matches[-1]) if process.returncode == 0 and matches else None
    return {
        "ate": ate,
        "seconds": round(seconds, 1),
        "returncode": process.returncode,
        "log": str(log),
    }


def check(suite_name: str, results: dict, reference: dict, tolerance: float) -> list[str]:
    """The regressions against the paper; empty if within tolerance."""
    ref = reference.get(suite_name, {}).get("ate")
    if not ref:
        return [f"{suite_name}: no reference numbers, nothing to check"] if results else []
    problems = []
    for seq, result in results.items():
        expected = ref.get(seq)
        if result["ate"] is None:
            problems.append(f"{seq}: failed (see {result['log']})")
        # The runs are not deterministic and small errors are noisy: allow an
        # absolute 1 cm on top of the relative tolerance.
        elif expected is not None and result["ate"] > expected * (1 + tolerance) + 0.01:
            problems.append(f"{seq}: ATE {result['ate']:.3f} > paper {expected:.3f}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("suite", choices=sorted(SUITES))
    parser.add_argument("--only", nargs="+", metavar="SEQ", help="only these sequences")
    parser.add_argument(
        "--root", type=pathlib.Path, help="dataset directory (default: as downloaded)"
    )
    parser.add_argument("--weights", help="droid.pth (default: @droid_weights)")
    parser.add_argument("--check", action="store_true", help="fail if worse than the paper")
    parser.add_argument("--tolerance", type=float, default=0.25, help="relative, for --check")
    parser.add_argument("--force", action="store_true", help="run even if the GPU looks too small")
    parser.add_argument(
        "--memory",
        choices=["auto", "upstream", "low"],
        default="auto",
        help=f"low: {' '.join(LOW_MEMORY_ARGS)} (auto: below {LOW_MEMORY_GB} GB)",
    )
    parser.add_argument("extra", nargs="*", help="after --: passed to every run")
    args = parser.parse_args()

    suite = SUITES[args.suite]
    dataset = datasets.DATASETS[suite.dataset]
    runfiles = Runfiles.Create()
    cwd = pathlib.Path(os.environ.get("BUILD_WORKING_DIRECTORY", "."))
    root = (cwd / (args.root or dataset.root)).resolve()
    weights = pathlib.Path(cwd / args.weights).resolve() if args.weights else None
    weights = weights or runfiles.Rlocation(os.environ["DROID_DEFAULT_WEIGHTS"])

    if not torch.cuda.is_available():
        print("No CUDA device (run gpu-check)", file=sys.stderr)
        return 1
    gpu = torch.cuda.get_device_properties(0)
    gpu_gb = gpu.total_memory / 2**30
    # The low-memory arguments cover upstream's 11 GB suites, not the 24 GB ones.
    if gpu_gb < dataset.min_gpu_gb and dataset.min_gpu_gb > LOW_MEMORY_GB and not args.force:
        print(
            f"{args.suite}: upstream needs about {dataset.min_gpu_gb} GB of GPU memory, "
            f"{gpu.name} has {gpu_gb:.1f} GB. Skipping (--force to try anyway).",
            file=sys.stderr,
        )
        return 0
    run_args = memory_args(args.memory, gpu_gb) + args.extra
    if run_args:
        print(f"{gpu.name} ({gpu_gb:.1f} GB): every run gets {' '.join(run_args)}")

    sequences = [s for s in suite.sequences if not args.only or s in args.only]
    if suite.dataset == "tartanair":
        mode = "stereo" if args.suite.endswith("stereo") else "mono"
        missing = [d for d in [mode, mode + "_gt"] if not (root / d).is_dir()]
    else:
        missing = [s for s in sequences if not (root / s).is_dir()]
    if missing:
        print(
            f"Missing under {root}: {' '.join(missing)} (//tools:download_dataset)", file=sys.stderr
        )
        return 1

    out = cwd / "results" / "benchmark" / args.suite
    out.mkdir(parents=True, exist_ok=True)
    script = runfiles.Rlocation(f"_main/evaluation_scripts/{suite.script}")
    results = {}
    for seq in sequences:
        cmd = [
            script,
            *suite.args(root, seq, runfiles),
            f"--weights={weights}",
            "--disable_vis",
            *run_args,
        ]
        results[seq] = run_sequence(suite, seq, cmd, out / f"{seq}.log")
        r = results[seq]
        ate = "FAILED" if r["ate"] is None else f"{r['ate']:.4f}"
        print(f"{seq:40s} ATE {ate:>8s} m  {r['seconds']:7.1f} s", flush=True)

    ates = [r["ate"] for r in results.values() if r["ate"] is not None]
    reference = json.loads(
        pathlib.Path(runfiles.Rlocation("_main/benchmark/reference.json")).read_text()
    )
    summary = {
        "suite": args.suite,
        "gpu": gpu.name,
        "torch": torch.__version__,
        "run_args": run_args,
        "mean_ate": float(np.mean(ates)) if ates else None,
        "failed": len(results) - len(ates),
        # ETH3D-SLAM's leaderboard metric (evaluation_scripts/parse_results.py).
        "auc_2cm": float(np.sum(np.clip(2.0 - 100 * np.array(ates), 0.0, None))),
        "auc_8cm": float(np.sum(np.clip(8.0 - 100 * np.array(ates), 0.0, None))),
        "paper_mean_ate": reference.get(args.suite, {}).get("mean_ate"),
        "sequences": results,
    }
    (out.parent / f"{args.suite}.json").write_text(json.dumps(summary, indent=2) + "\n")
    mean, paper = summary["mean_ate"], summary["paper_mean_ate"]
    print(f"mean ATE {mean} m (paper: {paper}), {summary['failed']} failed")
    print(f"Wrote {out.parent / (args.suite + '.json')}")

    if args.check:
        problems = check(args.suite, results, reference, args.tolerance)
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1 if any("nothing to check" not in p for p in problems) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
