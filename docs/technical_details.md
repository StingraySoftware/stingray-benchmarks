# Technical details

## Why eras

asv installs each benchmarked commit into a fixed set of environments.
Stingray v0.1 (2019) needs Python 3.7-era packages and an old setuptools,
while current `main` targets numpy 2.x. We split the history into eras, each with
its own environment, and send each commit range to the matching one:

| Era | Commits | asv environment name |
|---|---|---|
| 0 | v0.1 → v0.2 | `conda-py3.7-astropy3.2-matplotlib-base3.1-numba0.45-numpy1.16-scipy1.3-setuptools57-setuptools_scm-six-wheel-PIP_NO_BUILD_ISOLATIONfalse` |
| A | v0.2 → v1.0 | `conda-py3.8-astropy4.2-matplotlib-base3.3-numba0.53-numpy1.20-scipy1.6-setuptools-setuptools_scm-six-wheel` |
| B | v1.0 → v2.0.0 | `conda-py3.10-astropy5.3-matplotlib-base3.8-numba0.58-numpy1.26-scipy1.11-setuptools-setuptools_scm-wheel` |
| C | v2.0.0 → main | `conda-py3.12-astropy7.1-matplotlib-base3.10-numba0.62-numpy2.3-scipy1.16-setuptools-setuptools_scm-wheel` |

- Boundary releases (v0.2, v1.0, v2.0.0) are run in both adjacent eras. The jump
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
  the pinned packages. Eras 0 and A add `six`, which v0.1–v0.3 import.
- Era 0 pins setuptools 57: v0.1 builds with astropy-helpers, which uses
  `use_2to3`, removed in setuptools 58. `PIP_NO_BUILD_ISOLATION=false`
  (pip's confusingly named switch to *disable* build isolation) makes pip
  build with that setuptools instead of downloading the newest one. v0.2
  switched to setuptools_scm and also builds there.

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
- Stingray v0.1 averaged spectra accept only light curves (their `__init__`
  has no `dt`). There, `_compat.averaged_spectrum_from_events` bins the
  events with `to_lc(dt)` first, so the "from events" benchmarks include the
  binning, as newer versions do internally. Checked on 2026-09-17 by parsing
  the source of all 259 commits the runs can touch: the 36 commits from v0.1
  up to v0.2 have neither `dt` nor event support, all later ones have both,
  and none takes `**kwargs`.
- Input arrays come from `benchmarks/_data.py`, not from `setup()` code.
  Building Stingray objects in `setup()` (not `setup_cache`) confines any
  API breakage to the benchmarks that depend on it.
- asv identifies a benchmark by a hash of the source of the benchmark
  method, `setup` and `setup_cache` (not of helper modules). Editing those
  makes asv discard that benchmark's existing results.
- Sizes are asv parameters (1e6 and 1e7 events or bins). The averaged
  spectra run in two regimes: `few_long_segments` (2×1e7 events, 1000 s,
  dt=0.1 s, 100 s segments) and `many_short_segments` (2×1e6 events,
  3000 s, dt=1 ms, 3 s segments).
- `LightcurveSuite` passes `dt` and `gti` in both benchmarks, so the only
  difference between them is `skip_checks`.
- numba compiles functions on first call; asv always makes at least one
  untimed warm-up call, so compilation is not measured.

## Tests

- `tests/test_benchmarks_smoke.py` calls every benchmark once on tiny data
  (`STINGRAY_BENCH_SMALL=1`, written to a temporary data directory). Run it
  with the Python of an era environment; it is skipped without Stingray.
- `tests/test_compat.py` and `tests/test_run_history.py` need neither
  Stingray nor numpy.
- `tests/test_data.py` checks generation, reloading, corruption detection,
  and reads reference files written by the numpy of every era.
- To run pytest in an era environment without adding it there:
  `python -m pip install --target <dir> pytest`, then `PYTHONPATH=<dir>`.

## Benchmark data

- Each array is generated with `np.random.RandomState` and a fixed seed,
  verified against a SHA-256 checksum registered in `_data.CHECKSUMS`, and
  saved to `data/<name>.npy` (about 430 MB, not in git; override the location
  with `STINGRAY_BENCH_DATA`). Later loads verify the checksum again; any
  mismatch raises an error, so a benchmark never runs on different data.
- The checksum covers dtype, shape and array bytes, not the `.npy` header.
- Files are written in `.npy` format 1.0 with `allow_pickle=False`, atomically
  (temporary file + rename).
- Verified on 2026-09-17 with `tools/check_data_compat.py`: numpy 1.16.6,
  1.20.3, 1.26.4 and 2.3.5 each generated all 19 datasets with the
  registered checksums (so RandomState output is identical), and each read
  all 95 files (4 writers plus `data/`) with 0 mismatches. All files had
  format 1.0. Rerun the check when adding an era or changing a numpy pin.
- Registering a new dataset: run its generation with
  `STINGRAY_BENCH_RECORD=1`, which prints missing checksums instead of
  raising, and add them to `CHECKSUMS`.

## Commit selection (`run_history.py`)

- **Releases**: tags matching `vX.Y[.Z...]` (no rc/beta/dev) that are
  reachable from the era's end and descend from its start. Tags made only on
  side branches (v1.1.2.x, v2.2.7) are not reachable from `main` and are
  skipped.
- **History**: `git rev-list --first-parent start..end` plus `start`, i.e.
  roughly one commit per merged pull request. As of 2026-09 this is 36 (0),
  91 (A), 89 (B) and 74 (C) commits. v2.0.0 was tagged on a release branch, so era B
  follows that branch in its last stretch.
- `--steps N` thins the history evenly (asv's own `--steps`); releases are
  always run separately, so thinning never drops them.
- `--new` uses asv's `NEW` range in era C: commits newer than the latest one
  benchmarked on this machine.
- Every call uses `--skip-existing-successful`, so reruns only fill gaps.
  A failing commit makes the exit code non-zero but does not stop the run.
- `NUMBA_NUM_THREADS`, `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and
  `MKL_NUM_THREADS` default to 1 to reduce timing noise.

## Automation

- **Local (history):** `tools/systemd/` runs `run_history.py --new --publish`
  weekly on a fixed machine. One machine gives comparable numbers over years;
  asv files results by machine name, so a different machine is a new series.
- **GitHub Actions (relative check):** `asv continuous <latest release> main
  --factor 1.2` runs both commits back to back on the same runner. GitHub's
  shared runners differ from run to run by 10–20%, but within one job the
  two commits see the same hardware, so the ratio is meaningful even when
  absolute times are not. The latest release is the highest `vX.Y.Z` tag.
- `tools/conda-shim` finds micromamba via `$MICROMAMBA`, `$MAMBA_EXE` (set
  by `mamba-org/setup-micromamba`), `PATH`, then `~/.local/bin/micromamba`.

## Publishing

- `asv gh-pages` (asv 0.6.5) runs `asv publish`, creates a throwaway git
  repository inside `html/`, commits the site there and fetches it into the
  local `gh-pages` branch. The working copy and `main` are never touched.
- Without `--rewrite`, the new commit stacks on the *local* `gh-pages`
  branch. If there is none, asv starts an unrelated history that GitHub
  rejects on a normal push; create it first from `origin/gh-pages`.
- With `--rewrite`, `gh-pages` becomes a single commit and needs a force-push.
- `run_history.py` never passes anything that pushes: `--gh-pages` and
  `--rewrite` both call `asv gh-pages --no-push`.
- On 2026-09-17 the 2024 site (Python 3.11 runs whose results are not in
  this repository) was replaced with `--rewrite` and a force-push.
- The weekly systemd service syncs `gh-pages` from `origin` *before* running
  (`ExecStartPre`), so `--gh-pages` stacks on the published site. It commits
  results with `git commit -- results`, which ignores anything else staged,
  and does so in `ExecStopPost`, which runs even when `run_history.py` exits
  non-zero because one commit failed.
