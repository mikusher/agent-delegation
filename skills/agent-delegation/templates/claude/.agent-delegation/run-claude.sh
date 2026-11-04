#!/bin/sh
set -eu
if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code CLI is not available in PATH" >&2
  exit 2
fi
exec claude --model @@LEADER@@ "$@"
