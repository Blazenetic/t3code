#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "t3b-sync"


def run(*args: str, cwd: Path, check: bool = True, env: dict[str, str] | None = None):
    command_env = os.environ.copy()
    command_env.update(
        {
            "GIT_AUTHOR_NAME": "Fixture Author",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture Committer",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
            "GIT_EDITOR": "true",
            "GIT_SEQUENCE_EDITOR": "true",
        }
    )
    if env:
        command_env.update(env)
    result = subprocess.run(
        args,
        cwd=cwd,
        env=command_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        raise AssertionError(f"{' '.join(args)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def git(repo: Path, *args: str, check: bool = True):
    return run("git", *args, cwd=repo, check=check)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


class Fixture:
    def __init__(self, root: Path, *, conflicting: bool = False):
        self.root = root
        self.source = root / "source"
        self.origin = root / "origin.git"
        self.upstream = root / "upstream.git"
        self.repo = root / "work"

        git(root, "init", "--initial-branch=main", self.source.as_posix())
        write(self.source / "base.txt", "base\n")
        git(self.source, "add", "base.txt")
        git(self.source, "commit", "-m", "base")
        git(root, "init", "--bare", self.origin.as_posix())
        git(root, "init", "--bare", self.upstream.as_posix())
        git(self.source, "remote", "add", "origin-fixture", self.origin.as_posix())
        git(self.source, "remote", "add", "upstream-fixture", self.upstream.as_posix())
        git(self.source, "push", "origin-fixture", "main")
        git(self.source, "push", "upstream-fixture", "main")
        git(self.origin, "symbolic-ref", "HEAD", "refs/heads/main")
        git(self.upstream, "symbolic-ref", "HEAD", "refs/heads/main")

        git(root, "clone", self.origin.as_posix(), self.repo.as_posix())
        git(self.repo, "remote", "set-url", "origin", "https://github.com/Blazenetic/t3code")
        git(self.repo, "remote", "add", "upstream", "https://github.com/pingdotgg/t3code.git")
        git(self.repo, "remote", "set-url", "--push", "upstream", "no_push")
        git(self.repo, "config", f"url.file://{self.origin}.insteadOf", "https://github.com/Blazenetic/t3code")
        git(self.repo, "config", f"url.file://{self.upstream}.insteadOf", "https://github.com/pingdotgg/t3code.git")
        git(self.repo, "fetch", "upstream")

        git(self.repo, "switch", "-c", "blazenetic", "main")
        write(self.repo / "downstream.txt", "downstream\n")
        git(self.repo, "add", "downstream.txt")
        git(self.repo, "commit", "-m", "downstream")
        git(self.repo, "switch", "-c", "feature/topic")
        write(self.repo / "feature.txt", "feature\n")
        git(self.repo, "add", "feature.txt")
        git(self.repo, "commit", "-m", "feature")

        if conflicting:
            git(self.source, "switch", "main")
            write(self.source / "downstream.txt", "upstream version\n")
        else:
            write(self.source / "upstream.txt", "upstream\n")
        git(self.source, "add", ".")
        git(self.source, "commit", "-m", "upstream advance")
        git(self.source, "push", "upstream-fixture", "main")

    def tool(self, command: str | None = None):
        args = [SCRIPT.as_posix()]
        if command:
            args.append(command)
        return run(*args, cwd=self.repo, check=False, env={"T3B_SYNC_TIMESTAMP": "20260915-120000"})


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="t3b-sync-test-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_default_status_is_read_only_and_does_not_fetch(self):
        fixture = Fixture(self.root)
        before = git(fixture.repo, "rev-parse", "upstream/main").stdout.strip()
        result = fixture.tool()
        after = git(fixture.repo, "rev-parse", "upstream/main").stdout.strip()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mode: read-only", result.stdout)
        self.assertEqual(before, after)

    def test_fetch_is_explicit_and_guarded(self):
        fixture = Fixture(self.root)
        wanted = git(fixture.source, "rev-parse", "main").stdout.strip()
        self.assertNotEqual(git(fixture.repo, "rev-parse", "upstream/main").stdout.strip(), wanted)
        result = fixture.tool("fetch")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(fixture.repo, "rev-parse", "upstream/main").stdout.strip(), wanted)
        self.assertIn("no local branch was integrated or pushed", result.stdout)

    def test_legacy_apply_refuses_without_changing_branches(self):
        fixture = Fixture(self.root)
        before = git(fixture.repo, "show-ref").stdout
        result = fixture.tool("apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retired", result.stderr)
        self.assertEqual(git(fixture.repo, "show-ref").stdout, before)

    def test_refuses_wrong_remote_and_upstream_push_configuration(self):
        fixture = Fixture(self.root)
        git(fixture.repo, "remote", "set-url", "origin", "https://github.com/someone/t3code")
        result = fixture.tool("fetch")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe origin", result.stderr)
        git(fixture.repo, "remote", "set-url", "origin", "https://github.com/Blazenetic/t3code")
        git(fixture.repo, "remote", "set-url", "--push", "upstream", "https://github.com/pingdotgg/t3code.git")
        result = fixture.tool("fetch")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be exactly 'no_push'", result.stderr)



if __name__ == "__main__":
    unittest.main(verbosity=2)
