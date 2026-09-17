# Stingray benchmarks

Performance benchmarks for [Stingray](https://github.com/StingraySoftware/stingray),
run with [asv](https://asv.readthedocs.io) (airspeed velocity) across the
project history, from v0.1 (2019) to the current `main`.

Stingray's history spans Python 3.7 to 3.12+ and numpy 1.16 to 2.x, so no
single environment can install every commit. Commits are therefore split in
four **eras**, each benchmarked in its own pinned conda-forge environment.
All eras benchmark the same input data, created once in `data/` (about
430 MB, not in git) and verified by checksum on every load.
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
micromamba run -n asv python run_history.py --releases --history --steps 30 --dry-run
```

Benchmark all releases (a few hours):

```bash
micromamba run -n asv python run_history.py --releases --publish
```

Fill in the history, at most 30 commits per era (raise `--steps` later to
add more; existing results are kept):

```bash
micromamba run -n asv python run_history.py --history --steps 30 --publish
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

## Publishing

The website is live at <https://stingray.science/stingray-benchmarks/>,
served by GitHub Pages from the `gh-pages` branch of this repository.
Publishing takes three steps:

1. `asv publish` turns `results/` into a static website in `html/`
   (`run_history.py --publish`). Look at it locally with `asv preview`.
2. `asv gh-pages --no-push` builds the website again and commits it to the
   local `gh-pages` branch, without touching your working copy or `main`
   (`run_history.py --gh-pages`).
3. Pushing `gh-pages` to GitHub updates the website.

To update the website, stack a new commit on the published branch:

```bash
git fetch origin && git branch -f gh-pages origin/gh-pages
```

```bash
micromamba run -n asv python run_history.py --gh-pages
```

```bash
git push origin gh-pages
```

To start the branch over as a single commit (e.g. if it grows too large),
use `--rewrite` instead of `--gh-pages`; that always needs a force-push:

```bash
micromamba run -n asv python run_history.py --rewrite
```

```bash
git push -f origin gh-pages
```

## Weekly runs on a local machine

`tools/systemd/` has a systemd user service and timer that run every Sunday
at 02:00. Each run:

1. syncs the local `gh-pages` branch with GitHub's copy;
2. benchmarks commits on `main` newer than any benchmarked
   (`run_history.py --new --gh-pages`) and commits the website to `gh-pages`;
3. commits `results/` on `main` (only `results/`, nothing else you staged),
   even if some commit failed to benchmark.

Pushing is disabled until you have checked a run: then uncomment the two
`git push` lines. Pushing `main` also pushes any other local commits on
`main`, and needs stored GitHub credentials (the job runs unattended).
The weekly run is meant to add to a complete history: run
`run_history.py --history` once before enabling it.

After editing the unit files, copy them again and reload:

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
