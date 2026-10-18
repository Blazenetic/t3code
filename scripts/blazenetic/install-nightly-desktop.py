#!/usr/bin/env python3
"""Install a verified official nightly AppImage as an isolated remote client."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import urllib.request


def install(version):
    if not re.fullmatch(r"\d+\.\d+\.\d+-nightly\.\d+\.\d+", version):
        raise ValueError("An exact nightly version is required")
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("This installer supports Linux x86_64")
    home = Path.home()
    root = home / ".local/share/t3code-nightly-desktop"
    entry = home / ".local/share/applications/t3code-blazenetic-nightly.desktop"
    launcher = home / ".local/bin/t3b-nightly"
    for path in (entry, launcher):
        if path.exists() or path.is_symlink():
            raise ValueError(f"Preserving existing launcher: {path}; use the app updater")
    with urllib.request.urlopen(f"https://api.github.com/repos/pingdotgg/t3code/releases/tags/v{version}", timeout=30) as response:
        release = json.load(response)
    name = f"T3-Code-{version}-x86_64.AppImage"
    asset = next(a for a in release["assets"] if a["name"] == name)
    digest = asset.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("GitHub did not provide a SHA256 digest")
    root.mkdir(parents=True, exist_ok=True)
    # electron-updater renames versioned AppImages on update. A stable basename
    # is replaced in place, so the desktop launcher keeps working afterwards.
    destination = root / "T3-Code-Nightly.AppImage"
    staging = destination.with_suffix(".download")
    try:
        print(f"Downloading {name}...", flush=True)
        with urllib.request.urlopen(asset["browser_download_url"], timeout=60) as response, staging.open("wb") as output:
            checksum = hashlib.sha256()
            while chunk := response.read(1024 * 1024):
                checksum.update(chunk)
                output.write(chunk)
        if checksum.hexdigest() != digest.removeprefix("sha256:"):
            raise ValueError("AppImage checksum mismatch")
        staging.chmod(0o755)
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)
    # This is a new profile. Preserve any existing settings on repeat setup.
    profile = root / "profile"
    settings = profile / "userdata/desktop-settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    if not settings.exists():
        settings.write_text(json.dumps({"localEnvironmentEnabled": False, "updateChannel": "nightly"}) + "\n")
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text("#!/bin/sh\n" +
        "unset VITE_DEV_SERVER_URL VITE_HTTP_URL VITE_WS_URL T3CODE_HOST T3CODE_PORT\n" +
        f"export T3CODE_HOME={shlex.quote(str(profile))}\n" +
        f"exec {shlex.quote(str(destination))} \"$@\"\n")
    launcher.chmod(0o755)
    entry.parent.mkdir(parents=True, exist_ok=True)
    desktop_exec = str(launcher).replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$").replace("%", "%%")
    entry.write_text("[Desktop Entry]\nType=Application\nName=T3 Code Nightly — Blazenetic\n" +
                     "Comment=Nightly desktop client for your NetBird environment\n" +
                     f'Exec="{desktop_exec}"\nTerminal=false\nCategories=Development;\n')
    print(f"Installed {destination}\nLaunch: t3b-nightly (or KDE application menu).")
    print("Add the NetBird environment using a fresh t3b-netbird pair link.")


if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    install(parser.parse_args().version)
