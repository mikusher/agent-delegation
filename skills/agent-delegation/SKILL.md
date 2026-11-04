---
name: agent-delegation
description: Configure project-scoped leader/worker delegation for Codex (Sol/Terra), Claude Code (Opus/Haiku) or DeepSeek (Pro/Flash through Claude Code). Use to set up or verify native coding-agent collaboration without overriding existing project files.
---

# Agent Delegation

This skill prepares native project configuration. It does not install models, buy credits, access credentials, provide a new agent runtime, or establish security isolation.

## Contract

Input: platform (codex, claude, deepseek), existing target project directory, authorization to write, optionally model overrides for Codex/Claude.

Output: preview of new/conflicting files, applied configuration with no overwrite, static verification, and clear instructions for an actual runtime smoke test.

## Workflow

1. Confirm the user's actual target project. Never silently install into the skill's own repository or a different project.
2. Discover the installed CLI/harness and supported model entitlement without exposing secrets; distinguish a documented model ID from an available model on the account.
3. Review existing project instructions, configs and paths. Keep higher-priority instructions and permissions intact.
4. Run setup without --apply. Any existing content conflict requires human-guided merge; do not overwrite.
5. Only after authorization, run setup with --apply and then check with exactly the same options.
6. In the real client, verify coordinator and worker selections using agent/thread metadata. Run a small bounded task, inspect changes and test output. Do not claim the runtime was tested when only generated files were checked.
7. Report actual results, limitations, model/credential blockers and any observed latency/cost. No unsupported benchmark claims.

## Commands

From this repository root:

    python3 skills/agent-delegation/scripts/setup.py setup --platform codex --target /path/to/project
    python3 skills/agent-delegation/scripts/setup.py setup --platform codex --target /path/to/project --apply
    python3 skills/agent-delegation/scripts/setup.py check --platform codex --target /path/to/project

Other platform values: claude, deepseek. Optional --worktree applies only to Claude-compatible executor agents and requires an existing Git working tree. Codex and Claude accept --leader-model and --worker-model overrides. DeepSeek uses the documented fixed Pro/Flash routing pair.

## Delegation boundaries

The leader plans, defines acceptance checks, allocates non-overlapping ownership and verifies the result; workers implement or investigate bounded work with their permitted tools. Never imply that a worker's summary is proof of validation. No unapproved destructive operations, secret changes, merges, deployments or external publication. Escalate repeated worker failures instead of retrying indefinitely. For critical authorization/security paths, use an adequately capable reviewer and independent tests.

A skill file is only operational guidance; actual subagents, worktrees and model routing require real, supported capabilities in the selected client.
