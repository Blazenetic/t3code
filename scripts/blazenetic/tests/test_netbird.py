import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


loader = importlib.machinery.SourceFileLoader("netbird_tool", str(Path(__file__).parents[1] / "t3b-netbird"))
spec = importlib.util.spec_from_loader(loader.name, loader)
tool = importlib.util.module_from_spec(spec)
loader.exec_module(tool)


class NetbirdTests(unittest.TestCase):
    def test_address_requires_connected_management_and_safe_ipv4(self):
        for address, connected, accepted in [
            ("100.78.229.191/16", True, True), ("10.3.0.4/24", True, True),
            ("100.78.229.191/16", False, False), ("0.0.0.0", True, False),
            ("127.0.0.1", True, False), ("::1", True, False), ("224.0.0.1", True, False),
        ]:
            with self.subTest(address=address, connected=connected):
                result = subprocess.CompletedProcess([], 0, json.dumps({
                    "netbirdIp": address, "management": {"connected": connected}}))
                with patch.object(tool, "run", return_value=result):
                    if accepted:
                        self.assertEqual(tool.netbird_ip(), address.split("/")[0])
                    else:
                        with self.assertRaises(ValueError):
                            tool.netbird_ip()

    def test_changed_address_blocks_start(self):
        with patch.object(tool, "load_config", return_value={"ip": "100.64.0.1"}), patch.object(tool, "netbird_ip", return_value="100.64.0.2"):
            with self.assertRaisesRegex(ValueError, "address changed"):
                tool.preflight()

    def test_wrong_home_is_never_operated(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps({"base": str(Path.home() / ".t3")}))
            with patch.object(tool, "CONFIG", config):
                with self.assertRaisesRegex(ValueError, "Unexpected runtime home"):
                    tool.load_config()

    def test_other_service_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            unit = Path(directory) / "t3.service"
            dropin = Path(directory) / "dropin.conf"
            unit.write_text('Environment=T3CODE_HOME="/some/other/home"')
            dropin.write_text(tool.MARKER)
            with patch.object(tool, "UNIT", unit), patch.object(tool, "DROPIN", dropin), patch.object(tool, "load_config", return_value={}):
                with self.assertRaisesRegex(ValueError, "does not belong"):
                    tool.managed()

    def test_native_service_ownership_accepts_both_upstream_encodings(self):
        with tempfile.TemporaryDirectory() as directory:
            unit = Path(directory) / "t3.service"
            dropin = Path(directory) / "dropin.conf"
            dropin.write_text(tool.MARKER)
            for value in (str(tool.BASE), tool.quote(tool.BASE)):
                unit.write_text(f"[Service]\nEnvironment=T3CODE_HOME={value}\n")
                with patch.object(tool, "UNIT", unit), patch.object(tool, "DROPIN", dropin), patch.object(tool, "load_config", return_value={}):
                    tool.managed()

    def test_status_rejects_wildcard_or_missing_listener(self):
        config = {"ip": "100.64.0.1", "port": 13773}
        environment = f"T3CODE_HOST=100.64.0.1 T3CODE_PORT=13773 T3CODE_HOME={tool.BASE}"
        for sockets in ("", "LISTEN 0 511 0.0.0.0:13773 0.0.0.0:*\n"):
            results = [subprocess.CompletedProcess([], 0, environment), subprocess.CompletedProcess([], 0, sockets)]
            with patch.object(tool, "run", side_effect=results):
                with self.assertRaisesRegex(ValueError, "NetBird-only listener"):
                    tool.verify_listener(config)

    def test_launcher_collision_fails_before_download(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            launcher = home / ".local/bin/t3b-netbird"
            launcher.parent.mkdir(parents=True)
            launcher.write_text("user-owned")
            with patch.object(tool, "HOME", home), patch.object(tool, "UNIT", home / "unit"), patch.object(tool, "DROPIN", home / "dropin"), patch.object(tool, "CONFIG", home / "config"), patch.object(tool, "run") as run:
                with self.assertRaisesRegex(ValueError, "another installation"):
                    tool.install("0.0.41-nightly.20260914.1722", 13773)
                run.assert_not_called()
                self.assertEqual(launcher.read_text(), "user-owned")

    def test_loopback_development_listener_can_coexist(self):
        config = {"ip": "100.64.0.1", "port": 13773}
        environment = f"T3CODE_HOST=100.64.0.1 T3CODE_PORT=13773 T3CODE_HOME={tool.BASE}"
        sockets = "LISTEN 0 511 100.64.0.1:13773 0.0.0.0:*\nLISTEN 0 511 127.0.0.1:13773 0.0.0.0:*\n"
        results = [subprocess.CompletedProcess([], 0, environment), subprocess.CompletedProcess([], 0, sockets)]
        with patch.object(tool, "run", side_effect=results), patch("builtins.print"):
            tool.verify_listener(config)

    def test_uninstall_preserves_data_and_removes_only_owned_integration(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            base, tools = home / "runtime", home / "tools"
            base.mkdir(); tools.mkdir()
            data = base / "user-data"; data.write_text("keep")
            config, dropin, unit = tools / "config", home / "dropin", home / "unit"
            config.write_text(json.dumps({"base": str(base)}))
            dropin.write_text(tool.MARKER)
            unit.write_text(f"Environment=T3CODE_HOME={base}\n")
            (tools / "t3b-netbird").write_text("helper")
            link = home / ".local/bin/t3b-netbird"
            link.parent.mkdir(parents=True); link.symlink_to(tools / "t3b-netbird")
            with patch.multiple(tool, HOME=home, BASE=base, TOOLS=tools, CONFIG=config, DROPIN=dropin, UNIT=unit), patch.object(tool, "cli") as cli, patch.object(tool, "run"), patch.object(tool.sys, "argv", ["t3b-netbird", "uninstall"]), patch("builtins.print"):
                tool.main()
                cli.assert_called_once_with("service", "uninstall", "--base-dir", base)
            self.assertEqual(data.read_text(), "keep")
            self.assertFalse(dropin.exists())
            self.assertFalse(config.exists())
            self.assertFalse(link.is_symlink())

    def test_uninstall_failure_keeps_managed_configuration(self):
        with patch.object(tool, "load_config", return_value={}), patch.object(tool, "managed"), patch.object(tool, "cli", side_effect=subprocess.CalledProcessError(1, "t3")), patch.object(tool, "DROPIN") as dropin, patch.object(tool.sys, "argv", ["t3b-netbird", "uninstall"]):
            with self.assertRaises(subprocess.CalledProcessError):
                tool.main()
            dropin.unlink.assert_not_called()

    def test_systemd_escaping_and_injection_refusal(self):
        self.assertEqual(tool.quote('/a%h/"b'), '"/a%%h/\\"b"')
        with self.assertRaises(ValueError):
            tool.render_dropin("100.64.0.1", 13773, "/bin\nExecStart=bad")
        with self.assertRaises(ValueError):
            tool.render_dropin("100.64.0.1", 70000, "/bin")

    def test_cli_ignores_ambient_dev_and_live_home(self):
        with patch.object(tool, "load_config"), patch.object(tool, "run") as run, patch.dict(tool.os.environ, {"T3CODE_HOME": "/live", "T3CODE_HOST": "0.0.0.0", "VITE_HTTP_URL": "http://localhost"}):
            tool.cli("pair")
            env = run.call_args.kwargs["env"]
            self.assertEqual(env["T3CODE_HOME"], str(tool.BASE))
            self.assertNotIn("T3CODE_HOST", env)
            self.assertNotIn("VITE_HTTP_URL", env)


if __name__ == "__main__":
    unittest.main()
