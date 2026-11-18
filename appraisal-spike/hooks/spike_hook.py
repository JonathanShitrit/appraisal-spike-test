"""Spike hooks. Every call appends what it saw to /tmp/appraisal-spike.log.

session: SessionStart, returns additionalContext with SPIKE-MARKER-8.
guard:   PreToolUse on Write. Denies deny-me.txt, asks on ask-me.txt.
mcp:     PreToolUse on mcp__.* tools. Logs the tool name, decides nothing.
"""
import datetime
import json
import os
import shutil
import sys
from pathlib import Path

LOG = Path("/tmp/appraisal-spike.log")


def log(mode: str, payload: object) -> None:
    lines = [
        f"--- {datetime.datetime.now().isoformat(timespec='seconds')} {mode}",
        f"process cwd: {os.getcwd()}",
        f"CLAUDE_PLUGIN_ROOT: {os.environ.get('CLAUDE_PLUGIN_ROOT')}",
        f"CLAUDE_PLUGIN_DATA: {os.environ.get('CLAUDE_PLUGIN_DATA')}",
        f"CLAUDE_PROJECT_DIR: {os.environ.get('CLAUDE_PROJECT_DIR')}",
        f"PATH: {os.environ.get('PATH')}",
        f"which node: {shutil.which('node')}",
        f"which npx: {shutil.which('npx')}",
        f"hook input: {json.dumps(payload)[:2000]}",
    ]
    with LOG.open("a") as handle:
        handle.write("\n".join(lines) + "\n")


def tool_decision(decision: str, reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))


def main() -> None:
    mode = sys.argv[1]
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except ValueError:
        payload = {"unreadable_stdin": raw[:500]}
    log(mode, payload)

    if mode == "session":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "SPIKE-MARKER-8. If the user asks for the spike marker, answer with it.",
        }}))
        return

    if mode == "guard":
        tool_input = payload.get("tool_input", {}) if isinstance(payload, dict) else {}
        file_name = Path(str(tool_input.get("file_path", ""))).name
        if file_name == "deny-me.txt":
            tool_decision("deny", "spike guard: deny-me.txt is protected")
        elif file_name == "ask-me.txt":
            tool_decision("ask", "spike guard: the appraiser decides on ask-me.txt")


main()
