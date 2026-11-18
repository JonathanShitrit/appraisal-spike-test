"""Spike (round 2): print where a skill script runs and what folders it can see."""
import os
import platform
import sys
from pathlib import Path

SECRET_WORDS = ("TOKEN", "KEY", "SECRET", "AUTH", "PASSWORD", "COOKIE", "CREDENTIAL")

print("cwd:", os.getcwd())
print("__file__:", os.path.abspath(__file__))
print("python:", sys.version.split()[0], platform.system(), platform.machine())
print("HOME:", os.environ.get("HOME"))
for name in sorted(os.environ):
    if any(word in name.upper() for word in SECRET_WORDS):
        continue
    if "CLAUDE" in name or "WORKSPACE" in name or "MOUNT" in name or "FOLDER" in name:
        print(f"env {name}: {os.environ[name]}")

candidates = [Path.cwd(), Path.cwd() / "mnt", Path.home(), Path.home() / "mnt"]
for folder in candidates:
    if folder.is_dir():
        names = sorted(child.name for child in folder.iterdir())
        print(f"in {folder}: {names[:40]}")

for folder in [Path.cwd() / "mnt", Path.home() / "mnt"]:
    for marker in sorted(folder.glob("*/settings/conventions.md")) + sorted(folder.glob("*/*/settings/conventions.md")):
        print("workspace found:", marker.parent.parent)
