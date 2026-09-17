# Stingray benchmarks

Performance benchmarks for [Stingray](https://github.com/StingraySoftware/stingray),
run with [asv](https://asv.readthedocs.io) (airspeed velocity) across the
project history, from v0.3 (2021) to the current `main`.

Stingray's history spans Python 3.8 to 3.12+ and numpy 1.20 to 2.x, so no
single environment can install every commit. Commits are therefore split in
three **eras**, each benchmarked in its own pinned conda-forge environment.
See [docs/technical_details.md](docs/technical_details.md) for details.

## Setup

```bash
micromamba create -n asv -c conda-forge python=3.12 asv
```

asv builds its environments with micromamba, through a small wrapper:

```bash
export CONDA_EXE=$PWD/tools/conda-shim MAMBA_ROOT_PREFIX=$HOME/micromamba
```

```bash
micromamba run -n asv asv machine --yes
```

## Running by hand

Environment names (one per era) are listed in
[docs/technical_details.md](docs/technical_details.md).
Run a single release in its era, e.g. v0.3 in era A:

```bash
micromamba run -n asv asv run --show-stderr -E conda-py3.8-astropy4.2-matplotlib-base3.3-numba0.53-numpy1.20-scipy1.6-setuptools-setuptools_scm-six-wheel 'v0.3^!'
```

Then build and look at the web pages:

```bash
micromamba run -n asv asv publish
```

```bash
micromamba run -n asv asv preview
```
