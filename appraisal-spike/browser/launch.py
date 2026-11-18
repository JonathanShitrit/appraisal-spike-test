"""Spike (round 2): start Playwright MCP with a profile that survives sessions.

Runs as the MCP server command. Logs to /tmp/appraisal-spike.log, never to
stdout (stdout is the MCP channel), then replaces itself with npx.
"""
import datetime
import os
import shutil
from pathlib import Path

PLAYWRIGHT_MCP_VERSION = "0.0.85"
LOG = Path("/tmp/appraisal-spike.log")
PROFILE = Path.home() / "Library/Application Support/AppraisalCompsSpike/browser-profile"

PROFILE.mkdir(parents=True, exist_ok=True)
# The public registry, so a machine-wide npm setting (a company mirror) can't stall the start.
os.environ["npm_config_registry"] = "https://registry.npmjs.org/"
npx = shutil.which("npx") or "npx"
command = [
    npx, "-y", f"@playwright/mcp@{PLAYWRIGHT_MCP_VERSION}",
    "--user-data-dir", str(PROFILE),
    "--allowed-origins", "https://example.com;https://github.com",
]
with LOG.open("a") as handle:
    handle.write(f"--- {datetime.datetime.now().isoformat(timespec='seconds')} browser launch\n")
    handle.write(f"process cwd: {os.getcwd()}\n")
    handle.write(f"CLAUDE_PLUGIN_DATA: {os.environ.get('CLAUDE_PLUGIN_DATA')}\n")
    handle.write(f"command: {command}\n")
os.execvp(command[0], command)
