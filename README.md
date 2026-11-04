# Cheap Collaboration — Agent Delegation Kit

A project-scoped skill that sets up **strong leader + economical worker** collaboration in coding agents. It generates native project configuration, not a custom orchestration runtime.

| Platform | Leader | Worker | Harness |
| --- | --- | --- | --- |
| Codex | GPT-5.6 Sol | GPT-5.6 Terra | Codex native subagents |
| Claude Code | Opus | Haiku | Claude Code native subagents |
| DeepSeek | V4 Pro | Flash | Claude Code via DeepSeek Anthropic-compatible API |

## Quick start

Python 3.10+ required. The target must be an existing directory. Run from the repository root.

Preview (no writes):

    python3 skills/agent-delegation/scripts/setup.py setup --platform codex --target /path/to/project

Install project-local files:

    python3 skills/agent-delegation/scripts/setup.py setup --platform codex --target /path/to/project --apply

Verify generated configuration:

    python3 skills/agent-delegation/scripts/setup.py check --platform codex --target /path/to/project

Choose --platform codex, claude, or deepseek. For Claude/DeepSeek in a Git working tree, --worktree adds native worktree isolation to the executor; use it consistently for setup and check.

The skill instructions are in skills/agent-delegation/SKILL.md. Do not configure this source repository as the target unless deliberately testing against a disposable copy.

## Generated project files

Codex: AGENTS.md, .codex/config.toml, .codex/agents/delegated-executor.toml.

Claude Code: .claude/rules/delegation.md, .claude/agents/delegated-executor.md, .agent-delegation/run-claude.sh.

DeepSeek: analogous Claude Code files plus .agent-delegation/run-deepseek.sh.

Claude Code launcher: from the target directory, run sh .agent-delegation/run-claude.sh.

DeepSeek launcher: first set DEEPSEEK_API_KEY securely in your environment, then from the target directory run sh .agent-delegation/run-deepseek.sh. Do not commit credentials or paste real keys into scripts.

DeepSeek Pro/Flash delegation relies on the provider's documented Anthropic-model mapping. Claude Code is the actual subagent harness. This project does not claim native delegation in the DeepSeek model API.

## Non-destructive by design

- Dry-run is default; --apply creates missing files exclusively.
- Existing files with conflicting content fail closed, including existing AGENTS.md and Codex config.
- Generated files contain no tokens or secrets; user-level settings are untouched.
- Symlink destination components are refused; this is not a hardened sandbox against concurrent malicious local actors.
- Subagents inherit the host permissions; textual instructions are not isolation.
- No implicit deployment, destructive actions, pushes or merges.
- Static tests prove only installer behavior. Effective models, authorization, cost, quality and delegation must be verified in a real client.

For every delegated task, the leader must set boundaries and acceptance criteria; workers return changed paths, executed checks, actual results, and unresolved risks. The leader verifies the combined result. Small or security-critical tasks need not be delegated.

## Tests

    python3 -m unittest discover -s tests -v
    python3 -m compileall -q skills/agent-delegation/scripts

## Sources (verified 2026-11-04)

- Codex custom subagents: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Codex config: https://learn.chatgpt.com/docs/config-file/config-reference
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- GPT-5.6 Sol: https://developers.openai.com/api/docs/models/gpt-5.6-sol
- GPT-5.6 Terra: https://developers.openai.com/api/docs/models/gpt-5.6-terra
- DeepSeek Claude Code: https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/
- DeepSeek Anthropic mapping: https://api-docs.deepseek.com/guides/anthropic_api/

No affiliation with OpenAI, Anthropic, or DeepSeek. MIT licensed.
