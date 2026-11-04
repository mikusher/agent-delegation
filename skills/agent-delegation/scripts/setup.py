#!/usr/bin/env python3
"""Project-local delegation setup: dry-run first, exclusive writes, no user config changes."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL_DIR / "templates"
MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")
DEFAULTS = {
    "codex": ("gpt-5.6-sol", "gpt-5.6-terra"),
    "claude": ("opus", "haiku"),
    "deepseek": ("deepseek-v4-pro", "deepseek-flash"),
}
FILES = {
    "codex": ("AGENTS.md", ".codex/config.toml", ".codex/agents/delegated-executor.toml"),
    "claude": (".claude/agents/delegated-executor.md", ".claude/rules/delegation.md", ".agent-delegation/run-claude.sh"),
    "deepseek": (".claude/agents/delegated-executor.md", ".claude/rules/delegation.md", ".agent-delegation/run-deepseek.sh"),
}

class SetupError(Exception):
    pass

@dataclass(frozen=True)
class PlannedFile:
    relative: str
    content: str
    status: str

def model_id(raw: str) -> str:
    if not MODEL_ID.fullmatch(raw):
        raise SetupError("Invalid model ID. Allowed: alphanumeric, dot, hyphen, underscore, colon.")
    return raw

def choose_models(platform: str, leader: str | None, worker: str | None) -> tuple[str, str]:
    a, b = DEFAULTS[platform]
    a, b = model_id(leader or a), model_id(worker or b)
    if platform == "deepseek" and (a != "deepseek-v4-pro" or b != "deepseek-flash"):
        raise SetupError("DeepSeek profile supports only documented deepseek-v4-pro -> deepseek-flash routing")
    return a, b

def read_target(raw: str) -> Path:
    p = Path(raw).expanduser()
    if p.is_symlink():
        raise SetupError(f"Target cannot be a symlink: {p}")
    p = p.resolve(strict=True)
    if not p.is_dir():
        raise SetupError(f"Not a directory: {p}")
    return p

def verify_no_symlink(target: Path, relative: str) -> Path:
    node = target
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or ".." in parts:
        raise SetupError("Invalid destination path")
    for index, part in enumerate(parts):
        node = node / part
        if node.is_symlink():
            raise SetupError(f"Refusing symlink: {node}")
        if node.exists():
            if index < len(parts) - 1 and not node.is_dir():
                raise SetupError(f"Parent is not a directory: {node}")
            if index == len(parts) - 1 and not node.is_file():
                raise SetupError(f"Destination is not a file: {node}")
    return node

def check_git_worktree(target: Path) -> None:
    try:
        result = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, check=False, timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SetupError(f"Git check failed: {exc}") from exc
    if result.returncode or result.stdout.strip() != "true":
        raise SetupError("--worktree requires a Git working tree")

def render(platform: str, relative: str, leader: str, worker: str, worktree: bool) -> str:
    src = TEMPLATES / platform / relative
    text = src.read_text(encoding="utf-8")
    replacements = {
        "@@LEADER@@": leader,
        "@@WORKER@@": worker,
        "@@LEADER_JSON@@": json.dumps(leader),
        "@@WORKER_JSON@@": json.dumps(worker),
        "@@WORKTREE_LINE@@": "isolation: worktree\n" if worktree else "",
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    if re.search(r"@@[A-Z_]+@@", text):
        raise SetupError(f"Unresolved template field: {src}")
    return text

def plan(target: Path, platform: str, leader: str, worker: str, worktree: bool) -> list[PlannedFile]:
    if worktree:
        if platform == "codex":
            raise SetupError("--worktree applies only to Claude-compatible executor agents")
        check_git_worktree(target)
    output = []
    for relative in FILES[platform]:
        dest = verify_no_symlink(target, relative)
        content = render(platform, relative, leader, worker, worktree)
        if dest.exists():
            status = "unchanged" if dest.read_text(encoding="utf-8") == content else "CONFLICT"
        else:
            status = "create"
        output.append(PlannedFile(relative, content, status))
    return output

def install(target: Path, planned: list[PlannedFile]) -> None:
    if any(item.status == "CONFLICT" for item in planned):
        raise SetupError("Refusing to replace existing files:\n" +
                         "\n".join("  " + item.relative for item in planned if item.status == "CONFLICT"))
    created: list[Path] = []
    try:
        for item in planned:
            if item.status == "unchanged":
                continue
            dst = verify_no_symlink(target, item.relative)
            dst.parent.mkdir(parents=True, exist_ok=True)
            with dst.open("x", encoding="utf-8") as handle:
                handle.write(item.content)
            created.append(dst)
    except Exception:
        for dst in reversed(created):
            dst.unlink(missing_ok=True)
        raise

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("setup", "check"))
    parser.add_argument("--platform", choices=tuple(DEFAULTS), required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--leader-model")
    parser.add_argument("--worker-model")
    parser.add_argument("--worktree", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Write files; setup defaults to dry-run")
    args = parser.parse_args(argv)
    try:
        if args.command == "check" and args.apply:
            raise SetupError("--apply is invalid with check")
        target = read_target(args.target)
        leader, worker = choose_models(args.platform, args.leader_model, args.worker_model)
        pending = plan(target, args.platform, leader, worker, args.worktree)
        print(f"PROFILE: {args.platform}; leader={leader}; worker={worker}")
        for item in pending:
            print(f"{item.status.upper():9} {item.relative}")
        if args.command == "check":
            if any(i.status != "unchanged" for i in pending):
                raise SetupError("Not installed as expected; check detected missing or modified files")
            print("CHECK PASSED: files match expected templates (not a runtime smoke test)")
            return 0
        if args.apply:
            install(target, pending)
            print("APPLIED: project-local files created; verify runtime separately")
        else:
            print("DRY RUN: no files written; add --apply to install")
        return 0
    except (SetupError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
