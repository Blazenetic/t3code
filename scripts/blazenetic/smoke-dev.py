#!/usr/bin/env python3
"""Check isolated loopback development startup and always stop the spawned group."""
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


def main():
    repo = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(("T3CODE_", "VITE_")):
            env.pop(key)
    env.update(T3CODE_NO_BROWSER="true", T3CODE_DEV_AUTH_TOKEN=secrets.token_urlsafe(32), CI="true")
    with tempfile.TemporaryDirectory(prefix="t3b-smoke-") as temporary:
        root = Path(temporary)
        log = root / "startup.log"
        with log.open("w") as output:
            process = subprocess.Popen(
                [str(Path.home() / ".vite-plus/bin/vp"), "run", "dev", "--host", "127.0.0.1",
                 "--home-dir", str(root / "state")], cwd=repo, env=env,
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                start_new_session=True)
        try:
            deadline = time.monotonic() + 240
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Development exited before becoming ready.")
                match = re.search(r"\[dev-runner\].*?webPort=(\d+)", log.read_text())
                if match:
                    origin = f"http://127.0.0.1:{match[1]}"
                    try:
                        for path in ("/", "/.well-known/t3/environment"):
                            with opener.open(origin + path, timeout=3) as response:
                                if response.status != 200:
                                    raise RuntimeError("Unexpected development HTTP response.")
                        print("PASS: isolated development web and environment endpoints return HTTP 200.")
                        return
                    except (urllib.error.URLError, TimeoutError, ConnectionError):
                        pass
                time.sleep(0.5)
            raise RuntimeError("Development startup did not become ready within 240 seconds.")
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=15)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()


if __name__ == "__main__":
    main()
