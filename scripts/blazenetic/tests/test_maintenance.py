import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock

from test_sync import Fixture, git, write


M = runpy.run_path(str(Path(__file__).parents[1] / "t3b-maintain"))


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="t3b-maintenance-test-")
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.state.mkdir()
        self.identity = mock.patch.dict(os.environ, {
            "GIT_AUTHOR_NAME": "Maintenance Test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Maintenance Test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
        })
        self.identity.start()

    def tearDown(self):
        self.identity.stop()
        self.temp.cleanup()

    def prepare(self, fixture, **kwargs):
        return M["prepare"](fixture.repo, self.state, validator=lambda *_: None, **kwargs)

    def test_prepare_preserves_dirty_feature_and_customization_and_does_not_publish(self):
        f = Fixture(self.root)
        original = git(f.repo, "rev-parse", "HEAD").stdout
        hosted = git(f.origin, "rev-parse", "main").stdout
        write(f.repo / "unfinished.txt", "user work\n")
        record = self.prepare(f)
        self.assertEqual(record["result"], "ready")
        self.assertEqual(git(f.repo, "rev-parse", "HEAD").stdout, original)
        self.assertEqual(git(f.repo, "branch", "--show-current").stdout.strip(), "feature/topic")
        self.assertEqual((f.repo / "unfinished.txt").read_text(), "user work\n")
        self.assertEqual((self.state / "candidate/downstream.txt").read_text(), "downstream\n")
        self.assertTrue((self.state / "candidate/upstream.txt").is_file())
        self.assertEqual(git(f.origin, "rev-parse", "main").stdout, hosted)

    def test_accept_is_backed_up_and_fast_forwards_only_baseline(self):
        f = Fixture(self.root)
        original = git(f.repo, "rev-parse", "HEAD").stdout
        old = git(f.repo, "rev-parse", "blazenetic").stdout.strip()
        record = self.prepare(f)
        M["accept"](f.repo, self.state)
        self.assertEqual(git(f.repo, "rev-parse", "blazenetic").stdout.strip(), record["candidate"])
        self.assertEqual(git(f.repo, "rev-parse", "HEAD").stdout, original)
        backups = git(f.repo, "for-each-ref", "--format=%(objectname)", "refs/heads/backup/").stdout
        self.assertIn(old, backups)

    def test_mirror_only_updates_main_on_origin(self):
        f = Fixture(self.root)
        feature = git(f.repo, "rev-parse", "HEAD").stdout
        git(f.repo, "push", "origin", "blazenetic:refs/heads/historical")
        historical = git(f.origin, "rev-parse", "historical").stdout
        self.prepare(f, publish_main=True)
        self.assertEqual(git(f.origin, "rev-parse", "main").stdout,
                         git(f.upstream, "rev-parse", "main").stdout)
        self.assertEqual(git(f.origin, "rev-parse", "historical").stdout, historical)
        self.assertEqual(git(f.repo, "rev-parse", "HEAD").stdout, feature)

    def test_mirror_refuses_unique_hosted_commits(self):
        f = Fixture(self.root)
        git(f.repo, "push", "origin", "feature/topic:main")
        before = git(f.origin, "rev-parse", "main").stdout
        with self.assertRaisesRegex(M["SyncError"], "unique commits"):
            self.prepare(f, publish_main=True)
        self.assertEqual(git(f.origin, "rev-parse", "main").stdout, before)

    def test_conflict_is_preserved_and_rerun_refuses_to_overwrite_it(self):
        f = Fixture(self.root, conflicting=True)
        original = git(f.repo, "rev-parse", "HEAD").stdout
        with self.assertRaisesRegex(M["SyncError"], "conflict preserved"):
            self.prepare(f)
        tree = self.state / "candidate"
        self.assertTrue(git(tree, "diff", "--name-only", "--diff-filter=U").stdout)
        with self.assertRaisesRegex(M["SyncError"], "unfinished work"):
            self.prepare(f)
        self.assertEqual(git(f.repo, "rev-parse", "HEAD").stdout, original)

    def test_failed_checks_cannot_be_accepted_and_can_be_retried(self):
        f = Fixture(self.root)
        def fail(*_):
            raise M["SyncError"]("behavior check failed")
        with self.assertRaisesRegex(M["SyncError"], "behavior check failed"):
            M["prepare"](f.repo, self.state, validator=fail)
        with self.assertRaisesRegex(M["SyncError"], "No checked update"):
            M["accept"](f.repo, self.state)
        self.assertEqual(self.prepare(f)["result"], "ready")

    def test_candidate_edits_are_preserved_and_block_acceptance(self):
        f = Fixture(self.root)
        self.prepare(f)
        write(self.state / "candidate/downstream.txt", "user modification\n")
        with self.assertRaisesRegex(M["SyncError"], "changed after validation"):
            M["accept"](f.repo, self.state)

    def test_changed_or_checked_out_baseline_blocks_acceptance(self):
        f = Fixture(self.root)
        self.prepare(f)
        git(f.repo, "update-ref", "refs/heads/blazenetic", "HEAD")
        with self.assertRaisesRegex(M["SyncError"], "changed since validation"):
            M["accept"](f.repo, self.state)
        git(f.repo, "switch", "blazenetic")
        with self.assertRaisesRegex(M["SyncError"], "checked out"):
            M["accept"](f.repo, self.state)

    def test_unchanged_candidate_skips_expensive_checks(self):
        f = Fixture(self.root)
        first = self.prepare(f)
        validator = mock.Mock()
        second = M["prepare"](f.repo, self.state, validator=validator)
        validator.assert_not_called()
        self.assertEqual(first["candidate"], second["candidate"])

    def test_publish_uses_new_branch_and_refuses_non_fast_forward(self):
        f = Fixture(self.root)
        M["publish"](f.repo)
        remote = M["PUBLISHED_BRANCH"]
        self.assertEqual(git(f.origin, "rev-parse", remote).stdout,
                         git(f.repo, "rev-parse", "blazenetic").stdout)
        git(f.repo, "push", "origin", f"feature/topic:refs/heads/{remote}")
        with self.assertRaises(M["SyncError"]):
            M["publish"](f.repo)

    def test_lock_prevents_overlapping_maintenance(self):
        with M["locked"](self.state):
            with self.assertRaisesRegex(M["SyncError"], "already running"):
                with M["locked"](self.state):
                    self.fail("second writer acquired lock")

    def test_install_preserves_unmanaged_service(self):
        f = Fixture(self.root)
        fake_home = self.root / "home"
        unit = fake_home / ".config/systemd/user/t3b-maintain.service"
        write(unit, "unrelated user service\n")
        with mock.patch.object(Path, "home", return_value=fake_home):
            with self.assertRaisesRegex(M["SyncError"], "unmanaged unit"):
                M["install"](f.repo, self.state)
        self.assertEqual(unit.read_text(), "unrelated user service\n")

    def test_install_preserves_unmanaged_command(self):
        f = Fixture(self.root)
        fake_home = self.root / "home"
        launcher = fake_home / ".local/bin/t3b-maintain"
        write(launcher, "unrelated executable\n")
        with mock.patch.object(Path, "home", return_value=fake_home):
            with self.assertRaisesRegex(M["SyncError"], "unmanaged command"):
                M["install"](f.repo, self.state)
        self.assertEqual(launcher.read_text(), "unrelated executable\n")


if __name__ == "__main__":
    unittest.main()
