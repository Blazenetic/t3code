import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_sync import Fixture, git, write


SCRIPTS = Path(__file__).resolve().parents[1]


class DevelopmentTests(unittest.TestCase):
    def test_installed_launcher_uses_the_current_linked_worktree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = Fixture(root)
            script = fixture.repo / "scripts/blazenetic/t3b"
            write(script, (SCRIPTS / "t3b").read_text())
            script.chmod(0o755)
            launcher = root / "t3b-web"
            launcher.symlink_to(script)
            other = root / "other"
            git(fixture.repo, "worktree", "add", "-b", "feature/other", str(other), "main")
            home = root / "home"
            vp = home / ".vite-plus/bin/vp"
            write(vp, '#!/usr/bin/python3\nimport os\nprint(os.getcwd())\n')
            vp.chmod(0o755)
            result = subprocess.run([launcher], cwd=other, env=dict(os.environ, HOME=str(home)),
                                    capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.splitlines()[-1], str(other))

    def test_launchers_isolate_home_and_strip_origins(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            vp = home / ".vite-plus/bin/vp"
            vp.parent.mkdir(parents=True)
            vp.write_text('#!/usr/bin/python3\nimport json,os,sys\nprint(json.dumps({"args":sys.argv[1:],"env":{k:v for k,v in os.environ.items() if k.startswith(("T3CODE_","VITE_"))}}))\n')
            vp.chmod(0o755)
            env = dict(os.environ, HOME=str(home), T3CODE_HOME="/live", VITE_HTTP_URL="http://localhost", VITE_WS_URL="ws://localhost", VITE_DEV_SERVER_URL="http://localhost")
            for name, mode in [("t3b", "dev"), ("t3b-web", "dev"), ("t3b-desktop", "dev:desktop")]:
                result = subprocess.run([SCRIPTS / name, "--dry-run"], env=env, text=True, capture_output=True, check=True)
                recorded = json.loads(result.stdout.splitlines()[-1])
                self.assertEqual(recorded["env"], {})
                self.assertEqual(recorded["args"], ["run", mode, "--home-dir", str(SCRIPTS.parents[1] / ".t3"), "--dry-run"])
            result = subprocess.run([SCRIPTS / "t3b", "--home-dir=/live"], env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
