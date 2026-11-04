# DeepSeek delegation through Claude Code-compatible harness

Use the coordinator mapped to @@LEADER@@ for planning, task decomposition, code review and acceptance. Delegate bounded implementation to delegated-executor, mapped to @@WORKER@@ by the DeepSeek Anthropic-compatible API model mapping. Do not assume the models themselves spawn agents: Claude Code supplies the execution loop.

Use non-overlapping ownership for concurrent edits. Require actual commands and observed verification, not optimistic summaries. Reconsider the strategy after repeated worker failures. Review security-critical changes with a capable model and verify behavior independently. No unrelated repository integration, secret leakage, unauthorized writes, merging or deployment.
