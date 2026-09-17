"""Check that benchmark data are identical and readable across numpy versions.

Run with the Python of each era environment, first writing, then reading:

    python tools/check_data_compat.py write DIR   # generate all datasets into DIR/numpy<version>/
    python tools/check_data_compat.py read DIR    # verify every file under DIR

``write`` generates each registered dataset with this numpy, so a different
random stream fails the checksum already there. ``read`` loads every file
written by every numpy and verifies its checksum. Exit status is 1 on failure.
"""

import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from benchmarks import _data  # noqa: E402

GENERATORS = [
    (r"uniform_n(\d+)_t(\d+)_s(\d+)", lambda n, t, s: _data.uniform_events(n, t, s)),
    (r"merged_n(\d+)_t(\d+)", lambda n, t: _data.merged_events(n, t)),
    (r"poisson_n(\d+)_m(\d+)", lambda n, m: _data.poisson_counts(n, m)),
]


def write(root):
    _data.DATA_DIR = Path(root) / "numpy{}".format(np.__version__)
    for name in _data.CHECKSUMS:
        for pattern, make in GENERATORS:
            match = re.fullmatch(pattern, name)
            if match:
                make(*[int(x) for x in match.groups()])
                break
        else:
            raise ValueError("No generator for {}".format(name))
    print("numpy {}: wrote {} datasets to {}".format(np.__version__, len(_data.CHECKSUMS), _data.DATA_DIR))
    return 0


def read(root):
    failures = 0
    files = sorted(Path(root).glob("numpy*/*.npy"))
    for path in files:
        arr = np.load(str(path), allow_pickle=False)
        if _data.checksum(arr) != _data.CHECKSUMS[path.stem]:
            print("MISMATCH: {} read by numpy {}".format(path, np.__version__))
            failures += 1
    writers = sorted({p.parent.name for p in files})
    print("numpy {}: read {} files from {}: {} mismatches".format(
        np.__version__, len(files), ", ".join(writers), failures))
    return 1 if failures or not files else 0


if __name__ == "__main__":
    sys.exit({"write": write, "read": read}[sys.argv[1]](sys.argv[2]))
