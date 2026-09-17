import inspect
import itertools
import os
import warnings

import pytest

# A real submodule: the asv mirror in ./stingray would satisfy a bare "stingray".
pytest.importorskip("stingray.lightcurve")

# Must be set before importing the benchmarks: it shrinks every data size.
os.environ["STINGRAY_BENCH_SMALL"] = "1"

import benchmarks.benchmarks as bm  # noqa: E402
from benchmarks import _compat  # noqa: E402


def _suites():
    for _, cls in inspect.getmembers(bm, inspect.isclass):
        if cls.__module__ != bm.__name__:
            continue
        methods = [m for m in dir(cls) if m.startswith("time_")]
        params = getattr(cls, "params", None)
        if params is None:
            combos = [()]
        elif isinstance(params[0], list):
            combos = list(itertools.product(*params))
        else:
            combos = [(p,) for p in params]
        for method, combo in itertools.product(methods, combos):
            yield pytest.param(cls, method, combo, id=f"{cls.__name__}.{method}{list(combo)}")


@pytest.mark.parametrize("cls,method,combo", list(_suites()))
def test_benchmark_runs(cls, method, combo):
    """Every benchmark runs once on tiny data, calling setup_cache/setup the way asv does."""
    suite = cls()
    args = combo
    if hasattr(suite, "setup_cache"):
        args = (suite.setup_cache(),) + combo
    if hasattr(suite, "setup"):
        suite.setup(*args)
    getattr(suite, method)(*args)


def test_compat_passes_only_supported_keywords():
    """make_eventlist must not trigger Stingray's 'Unrecognized keywords' warning on old versions."""
    import numpy as np

    times = np.sort(np.random.default_rng(0).uniform(0, 10, 100))
    with warnings.catch_warnings():
        warnings.filterwarnings("error", message=".*Unrecognized keywords.*")
        _compat.make_eventlist(times, gti=[[0, 10]], skip_checks=True)
        _compat.make_eventlist(times, gti=[[0, 10]], skip_checks=False)
