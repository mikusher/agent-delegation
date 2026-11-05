# Cost-aware delegation policy

The main Claude agent (@@LEADER@@) owns requirements, planning, integration and security-sensitive review. **Do the task directly by default.** Delegate to delegated-executor (@@WORKER@@) only if a bounded independent investigation or change is expected to save more context/cost than its setup, handoff, verification and retry overhead. Skip delegation for small, coupled or already-understood tasks. Do not claim a requested model is the effective model without runtime evidence.

Start with zero workers; use one if justified, or up to two concurrently only for independent non-overlapping tasks. No nested delegation. Give each worker a minimal context, owned paths, exclusions, acceptance checks and concise evidence requirements. After one equivalent failed retry, reassess. The main agent verifies actual diffs, focused checks, security boundaries and final integration; summaries alone are not proof.

Before substantial coding, check once per execution environment for Ponytail, RTK (rtk-ai/rtk) and an explicitly identified Graphicy. Reuse installations; if absent, audit official/pinned sources and install only when authorized. Graphicy's upstream identity must be confirmed; never guess a package. Confirm workers actually see Ponytail rules and can use RTK; do not assume hooks, skills, PATH or environment settings are inherited. Prefer RTK for supported verbose shell output; inspect raw diagnostics when required. Missing optional tools must not prevent safe progress. Use Ponytail to minimize code, not security controls or tests.

Do not perform unapproved installs, unrelated writes, merges, deployments, credential changes, destructive actions or external communications. Keep output short and evidence-based.
