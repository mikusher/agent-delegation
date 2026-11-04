#!/usr/bin/env python3
"""Read-only, credential-safe check for conflicting Claude Code model/provider routing.

This is a conservative static preflight, not proof of model access or API reachability.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

EXPECTED_LEADER = "@@LEADER@@"
EXPECTED_WORKER = "@@WORKER@@"
OFFICIAL_ANTHROPIC_URL = "https://api.anthropic.com"
ROUTING_KEYS = {
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL_FORCE",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST",
}

def conflict(key: str, value: object) -> bool:
    if value is None or value == "":
        return False
    if key in ("CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY"):
        return str(value).strip().lower() not in ("0", "false", "no", "off")
    if key == "CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST":
        return bool(value)
    if key == "ANTHROPIC_BASE_URL":
        return not isinstance(value, str) or value.rstrip("/") != OFFICIAL_ANTHROPIC_URL
    if key in ("ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL"):
        return value != EXPECTED_LEADER
    if key in ("ANTHROPIC_DEFAULT_HAIKU_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL"):
        return value != EXPECTED_WORKER
    if key == "ANTHROPIC_DEFAULT_SONNET_MODEL":
        return not isinstance(value, str) or not value.startswith("claude-sonnet-")
    if key == "CLAUDE_CODE_SUBAGENT_MODEL_FORCE":
        # A forced subagent model changes the project's intended per-agent selection.
        return str(value).strip().lower() not in ("0", "false", "no", "off")
    return False

def main() -> int:
    issues: list[str] = []
    for key in sorted(ROUTING_KEYS):
        if key in os.environ and conflict(key, os.environ[key]):
            issues.append(f"{key} in process environment")

    # These are the usual local sources. Managed and embedding-host settings may
    # also apply; we cannot assert that this is the effective Claude Code config.
    config_root = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude").expanduser()
    project_root = Path(__file__).resolve().parents[1]
    sources = (
        ("user settings", config_root / "settings.json"),
        ("project settings", project_root / ".claude" / "settings.json"),
        ("project local settings", project_root / ".claude" / "settings.local.json"),
    )
    for label, path in sources:
        if not path.exists():
            continue
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(settings, dict):
                raise ValueError("settings must be an object")
        except (OSError, UnicodeError, ValueError):
            issues.append(f"unreadable/invalid {label} (configuration cannot be verified)")
            continue

        env = settings.get("env") or {}
        if not isinstance(env, dict):
            issues.append(f"invalid env object in {label}")
        else:
            for key in sorted(ROUTING_KEYS.intersection(env)):
                if conflict(key, env[key]):
                    issues.append(f"{key} in {label}")

        # Claude Code may remap model IDs independently of model and env settings.
        overrides = settings.get("modelOverrides")
        if overrides:
            issues.append(f"modelOverrides in {label} (review mapping before Anthropic launch)")

    if issues:
        print("CLAUDE ROUTING PREFLIGHT FAILED: native Anthropic profile cannot be verified.", file=sys.stderr)
        for item in sorted(set(issues)):
            print(f"  - {item}", file=sys.stderr)
        print(
            "Review shell exports and Claude Code settings; do not delete your existing "
            "local gateway setup. Re-run after selecting an explicit Anthropic session. "
            "No secret values were printed.",
            file=sys.stderr,
        )
        return 2

    print(
        f"CLAUDE ROUTING PREFLIGHT PASSED: expected {EXPECTED_LEADER} -> {EXPECTED_WORKER}; "
        "no conflicting overrides in inspected sources. "
        "API reachability, entitlement and managed settings are NOT verified."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
