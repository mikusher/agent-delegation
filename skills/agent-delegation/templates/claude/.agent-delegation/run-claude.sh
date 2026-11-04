#!/bin/sh
set -eu
if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code CLI is not available in PATH" >&2
  exit 2
fi
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required for Claude provider preflight" >&2
  exit 2
fi
python3 "$SCRIPT_DIR/check-claude.py" || exit 2
exec claude --model @@LEADER@@ "$@"
