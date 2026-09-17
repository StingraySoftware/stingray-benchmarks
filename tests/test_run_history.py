import subprocess

import pytest

import run_history


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture(scope="module")
def fake_repo(tmp_path_factory):
    """Linear history: v0.3, x, v1.0, v2.0.0rc1, v2.0.0, y (on main)."""
    repo = tmp_path_factory.mktemp("repo")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    hashes = {}
    for label in ["v0.3", "x", "v1.0", "v2.0.0rc1", "v2.0.0", "y"]:
        _git(repo, "commit", "-q", "--allow-empty", "-m", label)
        hashes[label] = _git(repo, "rev-parse", "HEAD")
        if label.startswith("v"):
            _git(repo, "tag", label)
    return repo, hashes


def test_release_tags_include_boundaries_and_skip_prereleases(fake_repo):
    """Both boundary releases belong to an era; rc/beta/dev tags are ignored."""
    repo, _ = fake_repo
    assert run_history.release_tags(repo, "v0.3", "v1.0") == ["v0.3", "v1.0"]
    assert run_history.release_tags(repo, "v1.0", "main") == ["v1.0", "v2.0.0"]


def test_history_commits_include_start_in_order(fake_repo):
    """Era history runs oldest to newest and includes its starting release."""
    repo, h = fake_repo
    assert run_history.history_commits(repo, "v0.3", "v1.0") == [h["v0.3"], h["x"], h["v1.0"]]
