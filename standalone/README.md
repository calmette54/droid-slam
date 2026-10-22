# droid-slam release

The DROID-SLAM sources with the CUDA extensions built by Bazel
(CUDA 12.8, PyTorch 2.7.0+cu128, x86_64 Linux, glibc >= 2.31).
See `UPSTREAM.md` for the upstream commits and changes.

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install --require-hashes -r requirements_lock.txt \
    --extra-index-url https://download.pytorch.org/whl/cu128
export PYTHONPATH=$PWD/site-packages:$PWD/droid_slam
python demo.py --imagedir=... --calib=calib/eth.txt --weights=droid.pth
```

The container image (`docker run --gpus all ...`) has everything installed.
