import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("desktop_install", Path(__file__).parents[1] / "install-nightly-desktop.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class DesktopInstallTests(unittest.TestCase):
    def test_checksum_failure_never_activates_download(self):
        version = "0.0.41-nightly.20260914.1722"
        metadata = {"assets": [{"name": f"T3-Code-{version}-x86_64.AppImage", "digest": "sha256:" + "0" * 64, "browser_download_url": "https://example.invalid/artifact"}]}
        with tempfile.TemporaryDirectory() as directory, patch.object(tool.Path, "home", return_value=Path(directory)), patch.object(tool.platform, "system", return_value="Linux"), patch.object(tool.platform, "machine", return_value="x86_64"), patch.object(tool.urllib.request, "urlopen", side_effect=[io.BytesIO(json.dumps(metadata).encode()), io.BytesIO(b"bad")]), patch("builtins.print"):
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                tool.install(version)
            self.assertFalse((Path(directory) / ".local/bin/t3b-nightly").exists())
            self.assertFalse(list(Path(directory).rglob("*.AppImage")))

    def test_installed_appimage_uses_stable_path_and_separate_profile(self):
        version = "0.0.41-nightly.20260914.1722"
        data = b"verified fixture"
        metadata = {"assets": [{"name": f"T3-Code-{version}-x86_64.AppImage", "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "browser_download_url": "https://example.invalid/artifact"}]}
        with tempfile.TemporaryDirectory() as directory, patch.object(tool.Path, "home", return_value=Path(directory)), patch.object(tool.platform, "system", return_value="Linux"), patch.object(tool.platform, "machine", return_value="x86_64"), patch.object(tool.urllib.request, "urlopen", side_effect=[io.BytesIO(json.dumps(metadata).encode()), io.BytesIO(data)]), patch("builtins.print"):
            tool.install(version)
            root = Path(directory) / ".local/share/t3code-nightly-desktop"
            self.assertEqual((root / "T3-Code-Nightly.AppImage").read_bytes(), data)
            launcher = (Path(directory) / ".local/bin/t3b-nightly").read_text()
            self.assertNotIn(version, launcher)
            settings = json.loads((root / "profile/userdata/desktop-settings.json").read_text())
            self.assertFalse(settings["localEnvironmentEnabled"])


if __name__ == "__main__":
    unittest.main()
