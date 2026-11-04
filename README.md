# Agent Delegation

**Install one skill. Ask your coding agent to configure cost-aware delegation.**

Agent Delegation ships a portable **agent skill** called `agent-delegation`. After installation, request setup in natural language. The skill prepares project-scoped, native leader/worker agents; there is no separate custom orchestration server.

| Environment | Leader / reviewer | Bounded executor | Runtime |
| --- | --- | --- | --- |
| Codex | GPT-5.6 Sol | GPT-5.6 Terra | Codex native agents |
| Claude Code | `claude-opus-5-5` | `claude-haiku-5-5` | Claude Code native subagents |
| DeepSeek | V4 Pro | Flash | Claude Code via DeepSeek Anthropic-compatible API |

Model access depends on your provider, account, CLI version and supported configuration. The DeepSeek profile requires a Claude Code-compatible harness, not just a model endpoint.

## Install the skill

Requires **Node.js 22.20+** for the optional `skills` CLI. Run the following in your target project's directory.

**Codex:**

```bash
npx skills add mikusher/agent-delegation --skill agent-delegation -a codex
```

**Claude Code** (also used as the DeepSeek-compatible harness):

```bash
npx skills add mikusher/agent-delegation --skill agent-delegation -a claude-code
```

The installer offers an interactive choice of skill scope. Use `-g` to make the skill available for every project in your user account, or omit it to install into the current project. To disable CLI telemetry, prefix the command with `DISABLE_TELEMETRY=1` on a POSIX shell. Review the repository before executing third-party packages or giving an agent filesystem access.

**After installing**, start/restart the coding-agent session if it does not discover the new skill immediately. The skill is not automatically applied to any project.

### Or ask the coding agent to install it

Paste this in Codex or Claude Code (no manual installation command required if that agent has approved shell/network tools):

> Install the `agent-delegation` skill from https://github.com/mikusher/agent-delegation for this agent. First inspect the skill and its executable files. Prefer project scope, unless I explicitly request a user-wide installation. Show the planned files and ask before any install, configuration change or network execution. Do not overwrite existing skills or config files. After installation, configure the **current project** using the supported platform, show a dry-run, ask before applying, run checks and report which model IDs were actually verified in the client. Do not assume test success or provider access from config files alone.

If the `skills` CLI is unavailable, an agent can instead clone the repository and copy the **entire** `skills/agent-delegation/` directory to a supported skill location. Copying only `SKILL.md` is **not sufficient**, because the skill includes a script and templates.

- Codex project: `.agents/skills/agent-delegation/`
- Codex user: `~/.agents/skills/agent-delegation/`
- Claude Code project: `.claude/skills/agent-delegation/`
- Claude Code user: `~/.claude/skills/agent-delegation/`

Never execute `curl | sh` or apply unreviewed remote installation scripts.

## Use the installed skill

In Claude Code, invoke `/agent-delegation`. In Codex, ask the agent to use the installed **agent-delegation** skill (on clients supporting explicit skill references, use `$agent-delegation`).

Example:

> Use agent-delegation to configure **this project** for Codex with Sol coordinating Terra. Preview changes and existing conflicts first. Once approved, apply only project-local files and verify the generated configuration. Then run a small read-only delegation smoke test if the runtime supports it.

For Claude Code: ask for **`claude-opus-5-5` → `claude-haiku-5-5`** (explicit Anthropic API IDs; no ambiguous `opus` or `haiku` aliases). For DeepSeek: ask for **V4 Pro → Flash through the Claude Code-compatible harness**.

**Two distinct actions:** installing the skill only registers reusable instructions with your coding agent; activating it in a project creates the project-specific agent configuration. Neither is a deployment.

## Direct setup (optional)

A standalone Python 3.10+ installer is included for environments without agent skill support. When run from a checkout of this repository:

```bash
python3 skills/agent-delegation/scripts/setup.py setup --platform codex --target /path/to/project
python3 skills/agent-delegation/scripts/setup.py setup --platform codex --target /path/to/project --apply
python3 skills/agent-delegation/scripts/setup.py check --platform codex --target /path/to/project
```

`--platform` accepts `codex`, `claude`, `deepseek`. Optional `--worktree` is for Claude-compatible agents when the target is a Git worktree. `--leader-model` and `--worker-model` are available for Codex/Claude, while the DeepSeek provider mapping uses the documented model pair.

From an **installed** skill, the agent must use the script next to that skill's `SKILL.md`: `<installed-skill-dir>/scripts/setup.py`. It must not assume the original repository is still present.

### Files the configuration step creates

- **Codex** — `AGENTS.md`, `.codex/config.toml`, `.codex/agents/delegated-executor.toml`.
- **Claude Code** — `.claude/rules/delegation.md`, `.claude/agents/delegated-executor.md`, `.agent-delegation/run-claude.sh`, `.agent-delegation/check-claude.py`.
- **DeepSeek** — Claude-compatible files plus `.agent-delegation/run-deepseek.sh`.

DeepSeek requires `DEEPSEEK_API_KEY` securely supplied in the environment; never commit real credentials. The generated launcher is for the CLI and does not set up the Claude Desktop GUI.

## Claude: canonical IDs and provider preflight

The native Anthropic profile now uses **`claude-opus-5-5`** for planning and **`claude-haiku-5-5`** for the worker. These are official Claude API IDs (2026-11-04), not convenience aliases. That does **not** by itself select Anthropic's API: your existing Claude Code settings, environment, gateway or managed policy can still redirect a request.

From the **target project directory**, check routing first (no network calls or secrets displayed):

```bash
python3 .agent-delegation/check-claude.py
```

Then launch through the generated wrapper; it runs the preflight before invoking Claude Code:

```bash
sh .agent-delegation/run-claude.sh
```

The preflight refuses known conflicting `ANTHROPIC_BASE_URL`, model mappings (including `ANTHROPIC_DEFAULT_HAIKU_MODEL`), alternate provider flags and `modelOverrides` in local/user project settings. It checks **environment variable names and configuration sources**, never prints values and never modifies your gateway settings. When a Jan/Ollama/other custom endpoint is configured, select an explicit appropriate provider profile or launch a clean Anthropic session. Do not blindly unset variables or remove a user's working local configuration.

**Important:** the preflight is conservative and static. Passing means only "no recognized conflict in inspected sources"; it does **not** prove actual endpoint selection, entitlement, token validity, network connectivity, managed settings, or subagent execution. Use `/status`, `claude doctor` and actual model/agent metadata to validate the running client. In particular, a `ConnectionRefused` error is a connectivity failure, not proof that a model ID is invalid.

### Existing installations

If the old kit already installed `model: haiku` or a launcher with `--model opus`, reinstalling from the revised skill will correctly report **CONFLICT** and will not overwrite those existing files. Review and migrate those two references to the explicit IDs, add the new preflight checker alongside the launcher, and compare the generated scripts. Run `check` again only after that review. Do not delete custom settings or tokens to make the check pass.

The **DeepSeek** adapter intentionally uses Claude-family routing aliases inside its explicitly configured DeepSeek provider environment; its `opus` invocation is **not** a native Anthropic model selection.

## Safety and current validation

The setup script defaults to **read-only preview**; `--apply` uses exclusive file creation and refuses conflicting contents. It does not edit account-level settings. It rejects symlinked paths found in the destination; this is not a sandbox against hostile concurrent local writers. Generated agent instructions cannot grant execution privileges.

Offline tests verify install previews, idempotence, conflicts, models, and project-scoped generation. They do **not** prove model access, delegation execution, correctness, cost savings, or supported behavior on every CLI version. Verify actual model and agent metadata in a real coding-agent session.

### Development

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q skills/agent-delegation/scripts
```

## References

- [Agent Skills CLI](https://github.com/vercel-labs/skills) — optional install/discovery manager (Node.js 22.20+)
- [Codex project skills location](https://developers.openai.com/api/reference/cli)
- [Claude Code custom skills](https://code.claude.com/docs/en/skills)
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- [DeepSeek Claude Code integration](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/)
- [DeepSeek Anthropic-compatible API](https://api-docs.deepseek.com/guides/anthropic_api/)

MIT licensed. Not affiliated with the model or agent providers.
