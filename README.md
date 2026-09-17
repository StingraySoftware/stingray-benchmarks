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

## Weekly runs on a local machine

`tools/systemd/` has a systemd user service and timer that run
`run_history.py --new --publish` every Sunday at 02:00. Edit
`WorkingDirectory` if needed, and uncomment the `ExecStartPost` lines to
commit (and push) the results automatically.

```bash
mkdir -p ~/.config/systemd/user && cp tools/systemd/stingray-benchmarks.* ~/.config/systemd/user/
```

```bash
systemctl --user daemon-reload && systemctl --user enable --now stingray-benchmarks.timer
```

User timers only run while you are logged in, unless lingering is enabled:

```bash
loginctl enable-linger $USER
```

Check the schedule and the last run:

```bash
systemctl --user list-timers stingray-benchmarks.timer
```

```bash
journalctl --user -u stingray-benchmarks.service -n 50
```

## GitHub Actions

`.github/workflows/asv-continuous.yml` runs every Monday (and on demand from
the Actions tab) and compares `main` with the latest Stingray release using
`asv continuous` in the era C environment. Benchmarks that got more than 20%
slower make the job fail; the full report is attached to the run as
`asv-continuous-report`. Shared runners are too noisy for a history graph, so
this job publishes nothing.

## Tests

Driver tests run in the `asv` environment:

```bash
micromamba run -n asv python -m pytest
```

Benchmark smoke tests need Stingray: run `pytest` with the Python of an asv
era environment in `env/`.
