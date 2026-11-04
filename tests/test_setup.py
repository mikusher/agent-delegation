"""Offline regression tests for safe project-local delegation setup."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/agent-delegation/scripts/setup.py"
spec = importlib.util.spec_from_file_location("delegation_setup", SCRIPT)
assert spec and spec.loader
setup = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = setup
spec.loader.exec_module(setup)

class SetupTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.temp = Path(tmp.name)
        self.target = self.temp / "project"
        self.target.mkdir()

    def invoke(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args, "--target", str(self.target)],
                              text=True, capture_output=True, check=False)

    def test_dry_run_is_read_only(self):
        result = self.invoke("setup", "--platform", "codex")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRY RUN", result.stdout)
        self.assertEqual(list(self.target.rglob("*")), [])

    def test_codex_install_and_check(self):
        self.assertEqual(self.invoke("setup", "--platform", "codex", "--apply").returncode, 0)
        self.assertEqual(self.invoke("check", "--platform", "codex").returncode, 0)
        import tomllib
        config = tomllib.loads((self.target / ".codex/config.toml").read_text())
        agent = tomllib.loads((self.target / ".codex/agents/delegated-executor.toml").read_text())
        self.assertEqual(config["model"], "gpt-5.6-sol")
        self.assertEqual(config["agents"]["default_subagent_model"], "gpt-5.6-terra")
        self.assertEqual(agent["model"], "gpt-5.6-terra")

    def test_claude_install_and_check(self):
        self.assertEqual(self.invoke("setup", "--platform", "claude", "--apply").returncode, 0)
        self.assertEqual(self.invoke("check", "--platform", "claude").returncode, 0)
        self.assertIn("model: claude-haiku-5-5", (self.target / ".claude/agents/delegated-executor.md").read_text())
        self.assertIn("claude --model claude-opus-5-5", (self.target / ".agent-delegation/run-claude.sh").read_text())
        self.assertTrue((self.target / ".agent-delegation/check-claude.py").exists())

    def claude_preflight(self, **overrides):
        environment = os.environ.copy()
        for key in list(environment):
            if key.startswith("ANTHROPIC_") or key.startswith("CLAUDE_CODE_"):
                environment.pop(key)
        environment["HOME"] = str(self.temp)
        environment.pop("CLAUDE_CONFIG_DIR", None)
        environment.update(overrides)
        checker = self.target / ".agent-delegation/check-claude.py"
        return subprocess.run([sys.executable, str(checker)],
                              cwd=self.target, env=environment, capture_output=True, text=True)

    def test_claude_preflight_accepts_clean_environment(self):
        self.assertEqual(self.invoke("setup", "--platform", "claude", "--apply").returncode, 0)
        result = self.claude_preflight()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NOT verified", result.stdout)

    def test_claude_preflight_refuses_local_endpoint_without_disclosure(self):
        self.assertEqual(self.invoke("setup", "--platform", "claude", "--apply").returncode, 0)
        url = "http://127.0.0.1:9000/secret-local-endpoint"
        result = self.claude_preflight(ANTHROPIC_BASE_URL=url)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ANTHROPIC_BASE_URL", result.stderr)
        self.assertNotIn(url, result.stderr)
        self.assertNotIn("secret-local-endpoint", result.stderr)

    def test_claude_preflight_refuses_jan_model_env_mapping(self):
        self.assertEqual(self.invoke("setup", "--platform", "claude", "--apply").returncode, 0)
        model = "janhq/Jan-code-4b-Q4_K_M"
        result = self.claude_preflight(ANTHROPIC_DEFAULT_HAIKU_MODEL=model)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ANTHROPIC_DEFAULT_HAIKU_MODEL", result.stderr)
        self.assertNotIn(model, result.stderr)

    def test_claude_preflight_refuses_model_mapping_in_user_settings(self):
        self.assertEqual(self.invoke("setup", "--platform", "claude", "--apply").returncode, 0)
        folder = self.temp / ".claude"
        folder.mkdir()
        (folder / "settings.json").write_text(
            json.dumps({"env": {"ANTHROPIC_BASE_URL": "http://localhost:8080"}}))
        result = self.claude_preflight()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("user settings", result.stderr)

    def test_claude_preflight_refuses_model_overrides_in_project(self):
        self.assertEqual(self.invoke("setup", "--platform", "claude", "--apply").returncode, 0)
        folder = self.target / ".claude"
        (folder / "settings.local.json").write_text(
            json.dumps({"modelOverrides": {"claude-haiku-5-5": "local-model"}}))
        result = self.claude_preflight()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("modelOverrides in project local settings", result.stderr)
        self.assertNotIn("local-model", result.stderr)

    def test_claude_preflight_rejects_other_provider_switch(self):
        self.assertEqual(self.invoke("setup", "--platform", "claude", "--apply").returncode, 0)
        result = self.claude_preflight(CLAUDE_CODE_USE_BEDROCK="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CLAUDE_CODE_USE_BEDROCK", result.stderr)

    def test_legacy_claude_install_is_not_silently_overwritten(self):
        self.assertEqual(self.invoke("setup", "--platform", "claude", "--apply").returncode, 0)
        path = self.target / ".claude/agents/delegated-executor.md"
        path.write_text(path.read_text().replace("claude-haiku-5-5", "haiku"))
        result = self.invoke("setup", "--platform", "claude", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFLICT", result.stdout)
        self.assertIn("model: haiku", path.read_text())

    def test_deepseek_install_and_check(self):
        self.assertEqual(self.invoke("setup", "--platform", "deepseek", "--apply").returncode, 0)
        self.assertEqual(self.invoke("check", "--platform", "deepseek").returncode, 0)
        script = (self.target / ".agent-delegation/run-deepseek.sh").read_text()
        self.assertIn("deepseek-v4-pro", script)
        self.assertIn("deepseek-flash", script)
        self.assertIn('ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"', script)
        self.assertNotIn("sk-", script)

    def test_idempotent_and_conflict_safe(self):
        self.assertEqual(self.invoke("setup", "--platform", "codex", "--apply").returncode, 0)
        self.assertEqual(self.invoke("setup", "--platform", "codex", "--apply").returncode, 0)
        target = self.target / "AGENTS.md"
        target.write_text("existing instructions\n")
        result = self.invoke("setup", "--platform", "codex", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFLICT", result.stdout)
        self.assertEqual(target.read_text(), "existing instructions\n")

    def test_reject_symlink(self):
        outside = self.temp / "outside"
        outside.mkdir()
        (self.target / ".codex").symlink_to(outside, target_is_directory=True)
        result = self.invoke("setup", "--platform", "codex", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing symlink", result.stderr)
        self.assertEqual(list(outside.iterdir()), [])

    def test_reject_model_injection(self):
        result = self.invoke("setup", "--platform", "codex",
                             "--leader-model", 'evil"\n[section]')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid model ID", result.stderr)

    def test_deepseek_mapping_is_locked(self):
        result = self.invoke("setup", "--platform", "deepseek", "--worker-model", "other")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("supports only", result.stderr)

    def test_check_fails_before_setup(self):
        result = self.invoke("check", "--platform", "claude")
        self.assertNotEqual(result.returncode, 0)

    def test_reject_worktree_without_git(self):
        result = self.invoke("setup", "--platform", "claude", "--worktree")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git working tree", result.stderr)

    def test_worktree_frontmatter(self):
        result = subprocess.run(["git", "init", "-q", str(self.target)], check=False)
        if result.returncode:
            self.skipTest("git unavailable")
        result = self.invoke("setup", "--platform", "claude", "--worktree", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("isolation: worktree",
                      (self.target / ".claude/agents/delegated-executor.md").read_text())

    def test_copied_skill_installs_from_outside_source_tree(self):
        import shutil

        installed = self.temp / ".agents" / "skills" / "agent-delegation"
        shutil.copytree(ROOT / "skills" / "agent-delegation", installed)
        copied_script = installed / "scripts" / "setup.py"

        for command, extra in (("setup", ["--apply"]), ("check", [])):
            result = subprocess.run(
                [sys.executable, str(copied_script), command, "--platform", "claude",
                 "--target", str(self.target), *extra],
                cwd=self.temp,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue((self.target / ".claude/agents/delegated-executor.md").exists())

    def test_custom_models_project_scoped(self):
        self.assertEqual(self.invoke("setup", "--platform", "codex", "--apply").returncode, 0)
        original = (self.target / ".codex/config.toml").read_bytes()
        with tempfile.TemporaryDirectory() as other:
            result = subprocess.run([sys.executable, str(SCRIPT), "setup", "--platform", "codex",
                                     "--target", other, "--leader-model", "gpt-6-sol",
                                     "--worker-model", "gpt-6-luna", "--apply"],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((self.target / ".codex/config.toml").read_bytes(), original)
            self.assertIn("gpt-6-sol", (Path(other) / ".codex/config.toml").read_text())

if __name__ == "__main__":
    unittest.main()
