"""Spike: print where a skill script runs from."""
import os

print("cwd:", os.getcwd())
print("__file__:", os.path.abspath(__file__))
print("CLAUDE_PLUGIN_DATA:", os.environ.get("CLAUDE_PLUGIN_DATA"))
print("CLAUDE_PLUGIN_ROOT:", os.environ.get("CLAUDE_PLUGIN_ROOT"))
