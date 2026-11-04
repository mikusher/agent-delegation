# Delegation policy

Use the main Claude model (@@LEADER@@) to plan and review. Delegate appropriate bounded tasks to the project subagent delegated-executor (@@WORKER@@).
Do not delegate for trivial work or when task handoff exceeds the likely benefit. Define acceptance checks and non-overlapping file ownership. The main agent validates behavior, security-sensitive boundaries and integration results. Worker summaries are not proof. Escalate after repeated failures; do not spend endless retries chasing lower token cost.
Preserve the user's requested target. Respect existing permissions and ask before irreversible operations, merges, deployments or external communications.
