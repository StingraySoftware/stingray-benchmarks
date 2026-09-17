#!/usr/bin/env python
"""Benchmark Stingray's history, sending each commit range to its era's environment.

Run from the asv micromamba environment, e.g.

    micromamba run -n asv python run_history.py --releases --dry-run

See README.md and docs/technical_details.md.
"""

import argparse
import datetime
import fcntl
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MIRROR = HERE / "stingray"
LOG_DIR = HERE / "logs"

# name, Python version of its asv environment, first and last commit
ERAS = [
    ("0", "3.7", "v0.1", "v0.2"),
    ("A", "3.8", "v0.2", "v1.0"),
    ("B", "3.10", "v1.0", "v2.0.0"),
    ("C", "3.12", "v2.0.0", "main"),
]
RELEASE_RE = re.compile(r"^v\d+(\.\d+)*$")


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.split()


def release_tags(repo, start, end):
    """Final release tags between ``start`` and ``end`` (both included), oldest first."""
    tags = [t for t in git(repo, "tag", "--merged", end) if RELEASE_RE.match(t)]
    tags = [
        t
        for t in tags
        if subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", start, t]
        ).returncode
        == 0
    ]
    return sorted(tags, key=lambda t: git(repo, "log", "-1", "--format=%ct", t)[0])


def history_commits(repo, start, end):
    """First-parent commits from ``start`` to ``end`` (both included), oldest first."""
    commits = git(repo, "rev-list", "--first-parent", "--reverse", f"{start}..{end}")
    return git(repo, "rev-parse", f"{start}^{{commit}}") + commits


def acquire_lock(path, blocking=True):
    """Take an exclusive lock on ``path``; return the open file, or None if busy.

    The lock is released when the returned file is closed or the process ends.
    """
    fobj = open(path, "w")
    try:
        fcntl.flock(fobj, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
    except BlockingIOError:
        fobj.close()
        return None
    return fobj


def environment_names():
    """Map Python version -> asv environment name, from asv.conf.json."""
    from asv.config import Config
    from asv.environment import get_environments

    conf = Config.load(str(HERE / "asv.conf.json"))
    return {env.python: env.name for env in get_environments(conf, None, verbose=False)}


def update_mirror():
    from asv.config import Config
    from asv.repo import get_repo

    get_repo(Config.load(str(HERE / "asv.conf.json"))).pull()


def run_asv(args, log):
    cmd = [sys.executable, "-m", "asv", *args]
    print("$", " ".join(cmd), file=log, flush=True)
    print("$", " ".join(cmd), flush=True)
    proc = subprocess.Popen(
        cmd, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in proc.stdout:
        sys.stdout.write(line)
        log.write(line)
    return proc.wait()


def asv_run_list(commits, env, extra, log):
    """Run asv on an explicit list of commits; a failing commit does not stop the run."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(commits) + "\n")
    try:
        return run_asv(["run", f"HASHFILE:{f.name}", "-E", env, *extra], log)
    finally:
        os.unlink(f.name)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--eras", default="0,A,B,C", help="Comma-separated eras (default: all)")
    parser.add_argument("--releases", action="store_true", help="Benchmark release tags")
    parser.add_argument("--history", action="store_true", help="Benchmark first-parent history")
    parser.add_argument("--steps", type=int, help="With --history: at most this many commits per era")
    parser.add_argument("--new", action="store_true", help="Commits on main newer than any benchmarked (era C)")
    parser.add_argument("--quick", action="store_true", help="One sample per benchmark (for testing)")
    parser.add_argument("--machine", help="asv machine name")
    parser.add_argument("--cpu-affinity", help="e.g. 2,3; passed to asv run")
    parser.add_argument("--publish", action="store_true", help="Run asv publish at the end")
    parser.add_argument("--gh-pages", action="store_true", help="Commit html to gh-pages (no push)")
    parser.add_argument(
        "--rewrite",
        action="store_true",
        help="Implies --gh-pages; replace the gh-pages branch with a single commit",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only print the commits per era")
    return parser.parse_args(argv)


def publish_commands(args):
    """asv commands that build the website; asv gh-pages runs publish itself."""
    if args.gh_pages or args.rewrite:
        return [["gh-pages", "--no-push"] + (["--rewrite"] if args.rewrite else [])]
    if args.publish:
        return [["publish"]]
    return []


def main(argv=None):
    args = parse_args(argv)

    os.environ.setdefault("CONDA_EXE", str(HERE / "tools" / "conda-shim"))
    os.environ.setdefault("MAMBA_ROOT_PREFIX", str(Path.home() / "micromamba"))
    # Single-threaded numerical libraries reduce timing noise.
    for var in ["NUMBA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]:
        os.environ.setdefault(var, "1")

    LOG_DIR.mkdir(exist_ok=True)
    lock = None
    if not args.dry_run:
        # Two runs at once would share environments and results and disturb
        # each other's timings: wait for any other run to finish.
        lock = acquire_lock(LOG_DIR / "run_history.lock", blocking=False)
        if lock is None:
            print("Another run_history.py is running; waiting for it to finish.", flush=True)
            lock = acquire_lock(LOG_DIR / "run_history.lock", blocking=True)

    update_mirror()
    envs = environment_names()
    extra = ["--skip-existing-successful", "--show-stderr"]
    if args.quick:
        extra.append("--quick")
    if args.machine:
        extra += ["--machine", args.machine]
    if args.cpu_affinity:
        extra += ["--cpu-affinity", args.cpu_affinity]

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    status = 0
    with open(LOG_DIR / f"run_history-{stamp}.log", "w") as log:
        for name, python, start, end in ERAS:
            if name not in args.eras.split(","):
                continue
            env = envs[python]
            if args.releases:
                tags = release_tags(MIRROR, start, end)
                print(f"Era {name} releases: {' '.join(tags)}", flush=True)
                if not args.dry_run:
                    status |= asv_run_list(tags, env, extra, log)
            if args.history:
                commits = history_commits(MIRROR, start, end)
                print(f"Era {name} history: {len(commits)} commits (steps={args.steps})", flush=True)
                if not args.dry_run:
                    steps = ["--steps", str(args.steps)] if args.steps else []
                    status |= asv_run_list(commits, env, extra + steps, log)
            if args.new and name == "C" and not args.dry_run:
                status |= run_asv(["run", "NEW", "-E", env, *extra], log)

        if args.dry_run:
            return 0
        for cmd in publish_commands(args):
            status |= run_asv(cmd, log)
    return status


if __name__ == "__main__":
    sys.exit(main())
