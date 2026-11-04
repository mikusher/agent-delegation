#!/bin/sh
set -eu
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  echo "DEEPSEEK_API_KEY is not configured; export it securely before launch" >&2
  exit 2
fi
if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code CLI is required for this DeepSeek adapter" >&2
  exit 2
fi
# Isolate this run from an existing Anthropic provider selection.
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"
export ANTHROPIC_MODEL="@@LEADER@@"
export ANTHROPIC_DEFAULT_OPUS_MODEL="@@LEADER@@"
export ANTHROPIC_DEFAULT_SONNET_MODEL="@@WORKER@@"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="@@WORKER@@"
unset CLAUDE_CODE_SUBAGENT_MODEL_FORCE
unset CLAUDE_CODE_SUBAGENT_MODEL
exec claude --model opus "$@"
