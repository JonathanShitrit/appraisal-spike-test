"""Spike hooks (round 2). Every call appends what it saw to /tmp/appraisal-spike.log.

session: SessionStart, returns additionalContext with SPIKE-MARKER-9.
guard:   PreToolUse on Write. Denies deny-me.txt, asks on ask-me.txt.
mcp:     PreToolUse on mcp__.* tools. Logs the tool name. On the sandbox Bash it
         denies a command naming deny-me.txt and asks on one naming ask-me.txt.
         On a browser navigate to example.net it denies.
"""
import datetime
import json
import os
import re
import shutil
import sys
from pathlib import Path

LOG = Path("/tmp/appraisal-spike.log")
SECRET_WORDS = ("TOKEN", "KEY", "SECRET", "AUTH", "PASSWORD", "COOKIE", "CREDENTIAL")
SHOWN_WORDS = ("CLAUDE", "COWORK", "WORKSPACE", "FOLDER", "PROJECT", "SESSION", "MOUNT", "HOME", "PWD", "USER")


def safe_env() -> dict:
    """Values only for names that look useful and not secret."""
    shown = {}
    for name in sorted(os.environ):
        upper = name.upper()
        if any(word in upper for word in SECRET_WORDS):
            continue
        if any(word in upper for word in SHOWN_WORDS):
            shown[name] = os.environ[name]
    return shown


def listing(folder: Path, depth: int) -> list:
    """Names under a folder, to the given depth. Names only, no contents."""
    found = []
    if not folder.is_dir():
        return found
    for child in sorted(folder.iterdir()):
        found.append(str(child))
        if depth > 1 and child.is_dir():
            found.extend(listing(child, depth - 1))
    return found[:60]


def host_paths_in_transcript(payload: dict) -> list:
    """Distinct /Users/... paths mentioned in the transcript so far."""
    transcript = Path(str(payload.get("transcript_path", "")))
    if not transcript.is_file():
        return ["transcript not found"]
    text = transcript.read_text(errors="replace")
    paths = sorted(set(re.findall(r"/Users/[^\"'\s\\]+", text)))
    return paths[:15]


def log(mode: str, payload: object) -> None:
    plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "/nonexistent"))
    lines = [
        f"--- {datetime.datetime.now().isoformat(timespec='seconds')} {mode}",
        f"process cwd: {os.getcwd()}",
        f"env names: {' '.join(sorted(os.environ))}",
        f"env values: {json.dumps(safe_env())}",
        f"which node: {shutil.which('node')}   which npx: {shutil.which('npx')}",
        f"near plugin root: {json.dumps(listing(plugin_root.parent.parent, 2))}",
        f"hook input: {json.dumps(payload)[:2000]}",
    ]
    if isinstance(payload, dict):
        lines.append(f"host paths in transcript: {json.dumps(host_paths_in_transcript(payload))}")
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
    if not isinstance(payload, dict):
        return
    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    if mode == "session":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "SPIKE-MARKER-9. If the user asks for the spike marker, answer with it.",
        }}))
        return

    if mode == "guard":
        file_name = Path(str(tool_input.get("file_path", ""))).name
        if file_name == "deny-me.txt":
            tool_decision("deny", "spike guard: deny-me.txt is protected")
        elif file_name == "ask-me.txt":
            tool_decision("ask", "spike guard: the appraiser decides on ask-me.txt")
        return

    if mode == "mcp":
        command = str(tool_input.get("command", ""))
        url = str(tool_input.get("url", ""))
        if tool_name.endswith("bash") and "deny-me.txt" in command:
            tool_decision("deny", "spike guard (bash): deny-me.txt is protected")
        elif tool_name.endswith("bash") and "ask-me.txt" in command:
            tool_decision("ask", "spike guard (bash): the appraiser decides on ask-me.txt")
        elif "example.net" in url:
            tool_decision("deny", "spike guard (browser): example.net is not enabled")


main()
