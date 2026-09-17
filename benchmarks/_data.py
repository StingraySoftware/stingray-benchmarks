"""Benchmark input data, created once and stored as checksum-verified .npy files.

Arrays are generated with numpy's legacy RandomState (whose stream numpy
keeps frozen), written in .npy format version 1.0 (readable by every numpy
we use) and verified against a registered SHA-256 checksum each time they are
generated or loaded. Files live in ``data/`` next to ``benchmarks/``, or in
the directory given by the STINGRAY_BENCH_DATA environment variable.

To register a new dataset, run the benchmarks' setup with
STINGRAY_BENCH_RECORD=1: missing checksums are printed instead of raising.
"""

import hashlib
import os
from pathlib import Path

import numpy as np

SEED = 20240419
DATA_DIR = Path(
    os.environ.get("STINGRAY_BENCH_DATA", Path(__file__).resolve().parent.parent / "data")
)

# SHA-256 from checksum(), recorded with numpy 2.3 and verified with 1.16-2.3.
CHECKSUMS = {
    "uniform_n1000000_t1000_s20240419": "2e6485fbafb0f675c6ab5f94055e3bcd8b3b27166359cbec3440cd6c89b6d46e",
    "poisson_n1000000_m100": "f1eead2f0f4a5266fe4e07cd5c0e6fd4b36752674af1adf9473596670ec5865b",
    "uniform_n10000000_t1000_s20240419": "f9f86e09b8b7ebcaf83ea9f5e550651d7fdd01f3e106c8a9f4d920c05b46d476",
    "poisson_n10000000_m100": "e53d257e3608c03c37c8c8ca5f44b094f803ffd122c620fe12dbe68aad0196a3",
    "uniform_n1000_t1000_s20240419": "3968f071635367d4b48abb0066c1b0ca3f98327c205f410cad3106e50f1a05d1",
    "poisson_n1000_m100": "1a6225b06b09c2d9378fcc00152464a6ed83bdcad03f8d4b3cf2b5431c3c73dc",
    "uniform_n10000_t1000_s20240419": "c50866d0a73e23a79410606068318ead0d185dba9a06ea0a3016abb509271ecd",
    "poisson_n10000_m100": "5e99fb1916a53f7682088db125dd17436e03ea8347e3f2b16ac7134059b0c859",
    "uniform_n10000000_t1000_s20240420": "b7202a8667a0eb8655725ee8b31ac648b6ceedb5abf5ccbd849de9e67b710a5a",
    "merged_n10000000_t1000": "140c8bbe3f43d564cc7ba582123e0c9932d3fb0342ddebdd1f799faa31057d26",
    "uniform_n1000000_t3000_s20240419": "bd681a91c82200ca797cf8d72a843ce9a289f3614fdd2ddfb775c3e80e3a1204",
    "uniform_n1000000_t3000_s20240420": "429adda24b46660febe5effd0a49daca84c9011f705b4eae34b02c24a0f331dd",
    "merged_n1000000_t3000": "3b3bbe3c5f1d602f8dabd46695700efedb3def3bf7d50e457bd95e207fb06bd6",
    "uniform_n2000_t100_s20240419": "ea1c5c2456d0f63b5005e7debf2994fc85364ffa6018da94281ad11019b90e3e",
    "uniform_n2000_t100_s20240420": "eb439940943c878f89433e75a5ad20429f5d814b366798542bbaee6e17dfba13",
    "merged_n2000_t100": "5f6bf044b5672acebc5d35787724a8f4fd96db2d302efd1c75bd68f3118fa227",
    "uniform_n2000_t30_s20240419": "d25a87f008e4de30d37232fb2681390b0e099aa1fef3e2e86175391939fd3fa0",
    "uniform_n2000_t30_s20240420": "a8aee0eb4b0f9791d76829714afae26a81deb239b252d2bfbf3bce2da8195112",
    "merged_n2000_t30": "4c1c8fa97be564021f750b6a5b371d56ef078dace8154106d1d3d813c24a728b",
}


def checksum(arr):
    """SHA-256 of dtype, shape and content; independent of the .npy header."""
    digest = hashlib.sha256()
    digest.update("{}{}".format(arr.dtype.str, arr.shape).encode())
    digest.update(np.ascontiguousarray(arr).tobytes())
    return digest.hexdigest()


def _verify(name, arr, source):
    expected = CHECKSUMS.get(name)
    actual = checksum(arr)
    if expected is None:
        if os.environ.get("STINGRAY_BENCH_RECORD"):
            print('    "{}": "{}",'.format(name, actual))
            return
        raise KeyError("No checksum registered for dataset {}".format(name))
    if actual != expected:
        raise RuntimeError("Checksum mismatch for {} ({})".format(name, source))


def save(path, arr):
    """Write ``arr`` as .npy format 1.0, atomically."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("{}.{}.tmp".format(path.name, os.getpid()))
    with open(str(tmp), "wb") as fobj:
        np.lib.format.write_array(fobj, arr, version=(1, 0), allow_pickle=False)
    os.replace(str(tmp), str(path))


def _cached(name, make):
    path = DATA_DIR / "{}.npy".format(name)
    if path.exists():
        arr = np.load(str(path), allow_pickle=False)
        _verify(name, arr, str(path))
        return arr
    arr = make()
    _verify(name, arr, "freshly generated")
    save(path, arr)
    return arr


def uniform_events(n, tmax, seed=SEED):
    """Sorted, uniformly distributed event times in [0, tmax), float64."""
    return _cached(
        "uniform_n{}_t{}_s{}".format(n, tmax, seed),
        lambda: np.sort(np.random.RandomState(seed).uniform(0, tmax, n)).astype("<f8"),
    )


def merged_events(n, tmax):
    """The two event lists with seeds SEED and SEED + 1, merged and sorted."""
    return _cached(
        "merged_n{}_t{}".format(n, tmax),
        lambda: np.sort(
            np.concatenate([uniform_events(n, tmax, SEED), uniform_events(n, tmax, SEED + 1)])
        ),
    )


def poisson_counts(n, mean=100):
    """Poisson-distributed counts, int64."""
    return _cached(
        "poisson_n{}_m{}".format(n, mean),
        lambda: np.random.RandomState(SEED).poisson(mean, size=n).astype("<i8"),
    )
