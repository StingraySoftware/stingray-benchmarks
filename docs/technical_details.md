# Technical details

## Why eras

asv installs each benchmarked commit into a fixed set of environments.
Stingray v0.3 (2021) needs numpy < 1.24 and Python 3.8-era packages, while
current `main` targets numpy 2.x. We split the history into eras, each with
its own environment, and send each commit range to the matching one:

| Era | Commits | asv environment name |
|---|---|---|
| A | v0.3 → v1.0 | `conda-py3.8-astropy4.2-matplotlib-base3.3-numba0.53-numpy1.20-scipy1.6-setuptools-setuptools_scm-six-wheel` |
| B | v1.0 → v2.0.0 | `conda-py3.10-astropy5.3-matplotlib-base3.8-numba0.58-numpy1.26-scipy1.11-setuptools-setuptools_scm-wheel` |
| C | v2.0.0 → main | `conda-py3.12-astropy7.1-matplotlib-base3.10-numba0.62-numpy2.3-scipy1.16-setuptools-setuptools_scm-wheel` |

- Boundary releases (v1.0, v2.0.0) are run in both adjacent eras. The jump
  between the two lines at a boundary estimates how much a change is due to
  the environment rather than to Stingray.
- Pins are exact to the minor version, so results within an era stay
  comparable over time. Changing a pin creates a new environment name, i.e.
  a new line in the plots.
- numba is installed in every era: Stingray is much faster with it, and an
  unrecorded numba change would look like a Stingray change.
- pyfftw is deliberately *not* installed: Stingray (v0.3 included) uses it when
  present, and leaving it out keeps the scipy FFT in every era.
- Stingray is installed with `pip install --no-deps`, so pip never alters
  the pinned packages. Era A adds `six`, which v0.3 still imports.

## Environments via micromamba

asv's `rattler` backend (asv 0.6.5) is incompatible with py-rattler ≥ 0.22,
so we use the `conda` backend with micromamba. asv decides between
`conda env create --yes` and the obsolete `--force` from the conda version
number; micromamba reports 2.x and receives `--force`, which it rejects.
`tools/conda-shim` rewrites that flag and calls micromamba. Set
`CONDA_EXE=<repo>/tools/conda-shim` before running asv.

## First validation (2026-09-17)

Quick run (one sample) of the original benchmarks on v0.3 (era A), v1.0
(era B), v2.0.0 and main (era C): all 14 benchmarks ran on all four commits.
Environments take 0.8–1.8 GB each; a quick run takes 1–2 min per commit.

## Benchmark design

- `benchmarks/_compat.py` detects features from call signatures, not from
  version numbers. Old `EventList` accepts `**kwargs` and only warns about
  unknown ones such as `skip_checks`; the warning alone tripled the
  "no checks" timing on v0.3. We now pass a keyword only if it is declared.
- Before v2.0, `EventList` did no checks, so `time_create_with_checks` and
  `time_create_no_checks` time the same code in eras A and B.
- Data are generated in `setup()` with `np.random.RandomState` and a fixed
  seed. RandomState's stream is frozen by numpy, so every era sees the
  same events. Building Stingray objects in `setup()` (not `setup_cache`)
  confines any API breakage to the benchmarks that depend on it.
- Sizes are asv parameters (1e6 and 1e7 events or bins). The averaged
  spectra run in two regimes: `few_long_segments` (2×1e7 events, 1000 s,
  dt=0.1 s, 100 s segments) and `many_short_segments` (2×1e6 events,
  3000 s, dt=1 ms, 3 s segments).
- `LightcurveSuite` passes `dt` and `gti` in both benchmarks, so the only
  difference between them is `skip_checks`.
- numba compiles functions on first call; asv always makes at least one
  untimed warm-up call, so compilation is not measured.

## Tests

`pytest` (run with the Python of an era environment) calls every benchmark
once on tiny data (`STINGRAY_BENCH_SMALL=1`), in a few seconds. It passes
on v0.3 (era A) and main (era C).
