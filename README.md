# Stingray benchmarks

Performance benchmarks for [Stingray](https://github.com/StingraySoftware/stingray),
run with [asv](https://asv.readthedocs.io) (airspeed velocity) across the
project history, from v0.3 (2021) to the current `main`.

Stingray's history spans Python 3.8 to 3.12+ and numpy 1.20 to 2.x, so no
single environment can install every commit. Commits are therefore split in
three **eras**, each benchmarked in its own pinned conda-forge environment.
See [docs/technical_details.md](docs/technical_details.md) for details.

## Setup (once per machine)

```bash
micromamba create -n asv -c conda-forge python=3.12 asv pytest
```

```bash
micromamba run -n asv asv machine --yes
```

## Running

`run_history.py` picks the right environment for each commit, skips commits
that already have results, keeps going if a commit fails, and logs to `logs/`.
It sets `CONDA_EXE` to `tools/conda-shim`, so asv builds environments with
micromamba.

See which commits would run, without running anything:

```bash
micromamba run -n asv python run_history.py --releases --history --steps 100 --dry-run
```

Benchmark all releases (a few hours):

```bash
micromamba run -n asv python run_history.py --releases --publish
```

Fill in the history, at most 100 commits per era:

```bash
micromamba run -n asv python run_history.py --history --steps 100 --publish
```

Only commits on `main` newer than anything benchmarked (for scheduled runs):

```bash
micromamba run -n asv python run_history.py --new --publish
```

Look at the plots:

```bash
micromamba run -n asv asv preview
```

Results in `results/` are meant to be committed to this repository.

## Tests

Driver tests run in the `asv` environment:

```bash
micromamba run -n asv python -m pytest
```

Benchmark smoke tests need Stingray: run `pytest` with the Python of an asv
era environment in `env/`.
