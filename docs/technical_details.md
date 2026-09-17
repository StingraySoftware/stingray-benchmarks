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
- pyfftw is deliberately *not* installed: Stingray v1.0+ uses it when
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
