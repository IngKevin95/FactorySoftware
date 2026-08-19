import json
from pathlib import Path

from factorysoftware.adapters.base import ProviderAdapter
from factorysoftware.adapters.claude_code import ClaudeCodeAdapter


class _FakeAdapter:
    name = "fake"

    def detect(self, project_root: Path) -> bool:
        return True

    def target_paths(self, project_root: Path, skill_ids: list[str]) -> dict[str, Path]:
        return {sid: project_root / f"{sid}.md" for sid in skill_ids}

    def render(self, skill_id: str, content_md: str) -> str:
        return content_md


def test_fake_adapter_satisfies_protocol(tmp_path: Path):
    adapter: ProviderAdapter = _FakeAdapter()
    assert adapter.detect(tmp_path) is True
    assert adapter.target_paths(tmp_path, ["a"]) == {"a": tmp_path / "a.md"}
    assert adapter.render("a", "x") == "x"


def test_claude_code_detect_true_when_dot_claude_dir(tmp_path: Path):
    (tmp_path / ".claude").mkdir()
    assert ClaudeCodeAdapter().detect(tmp_path) is True


def test_claude_code_detect_false_when_absent(tmp_path: Path):
    assert ClaudeCodeAdapter().detect(tmp_path) is False


def test_claude_code_target_paths_one_dir_per_skill(tmp_path: Path):
    paths = ClaudeCodeAdapter().target_paths(tmp_path, ["requirements-prd", "requirements-flujo"])
    assert paths["requirements-prd"] == tmp_path / ".claude" / "skills" / "requirements-prd" / "SKILL.md"
    assert paths["requirements-flujo"] == tmp_path / ".claude" / "skills" / "requirements-flujo" / "SKILL.md"


def test_claude_code_render_adds_frontmatter():
    rendered = ClaudeCodeAdapter().render("requirements-prd", "Hacé el PRD.")
    assert rendered.startswith("---\n")
    assert "name: requirements-prd" in rendered
    assert "description:" in rendered
    assert "Hacé el PRD." in rendered


def test_install_gitflow_hook_writes_guard_script(tmp_path: Path):
    written = ClaudeCodeAdapter().install_gitflow_hook(tmp_path)
    guard = tmp_path / ".claude" / "hooks" / "gitflow-guard.sh"
    assert guard in written
    assert guard.exists()
    assert "git commit" in guard.read_text(encoding="utf-8")
    assert "main" in guard.read_text(encoding="utf-8")


def test_install_gitflow_hook_registers_in_settings(tmp_path: Path):
    ClaudeCodeAdapter().install_gitflow_hook(tmp_path)
    settings_path = tmp_path / ".claude" / "settings.json"
    assert settings_path.exists()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    pretooluse = settings["hooks"]["PreToolUse"]
    assert any(entry["matcher"] == "Bash" for entry in pretooluse)
    # Verify complete entry structure
    bash_entry = next(e for e in pretooluse if e["matcher"] == "Bash")
    assert "hooks" in bash_entry
    assert isinstance(bash_entry["hooks"], list)
    assert len(bash_entry["hooks"]) > 0
    hook = bash_entry["hooks"][0]
    assert hook["type"] == "command"
    assert "command" in hook
    assert "gitflow-guard.sh" in hook["command"]


def test_install_gitflow_hook_merges_existing_settings(tmp_path: Path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        json.dumps({"otherSetting": True}), encoding="utf-8"
    )
    ClaudeCodeAdapter().install_gitflow_hook(tmp_path)
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert settings["otherSetting"] is True
    assert "hooks" in settings


def test_install_gitflow_hook_raises_on_malformed_json(tmp_path: Path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{ invalid json", encoding="utf-8")
    try:
        ClaudeCodeAdapter().install_gitflow_hook(tmp_path)
        assert False, "Expected ValueError to be raised"
    except ValueError as e:
        assert "malformed JSON" in str(e)
        assert "settings.json" in str(e)
        assert "fix or remove" in str(e)


def test_install_gitflow_hook_is_idempotent(tmp_path: Path):
    adapter = ClaudeCodeAdapter()
    # First call
    adapter.install_gitflow_hook(tmp_path)
    settings1 = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    first_count = len(settings1["hooks"]["PreToolUse"])

    # Second call
    adapter.install_gitflow_hook(tmp_path)
    settings2 = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    second_count = len(settings2["hooks"]["PreToolUse"])

    # Should not have added a duplicate
    assert first_count == second_count == 1
    # Verify it's still the same entry
    bash_entries = [e for e in settings2["hooks"]["PreToolUse"] if e["matcher"] == "Bash"]
    assert len(bash_entries) == 1


from factorysoftware.adapters import registry


class _AlwaysYes:
    name = "always_yes"
    def detect(self, project_root): return True
    def target_paths(self, project_root, skill_ids): return {}
    def render(self, skill_id, content_md): return content_md


class _AlwaysNo:
    name = "always_no"
    def detect(self, project_root): return False
    def target_paths(self, project_root, skill_ids): return {}
    def render(self, skill_id, content_md): return content_md


def test_detect_returns_all_matching_adapters(tmp_path: Path):
    found = registry.detect(tmp_path, adapters=[_AlwaysYes(), _AlwaysNo()])
    assert [a.name for a in found] == ["always_yes"]


def test_detect_returns_multiple_when_several_match(tmp_path: Path):
    found = registry.detect(tmp_path, adapters=[_AlwaysYes(), _AlwaysYes()])
    assert len(found) == 2


def test_detect_empty_when_none_match(tmp_path: Path):
    assert registry.detect(tmp_path, adapters=[_AlwaysNo()]) == []


def test_select_by_name_overrides_detection(tmp_path: Path):
    selected = registry.select(["always_no"], adapters=[_AlwaysYes(), _AlwaysNo()])
    assert [a.name for a in selected] == ["always_no"]


def test_select_warns_about_unrecognized_provider_names(capsys):
    selected = registry.select(["always_no", "typo_provider"], adapters=[_AlwaysYes(), _AlwaysNo()])
    assert [a.name for a in selected] == ["always_no"]
    err = capsys.readouterr().err
    assert "typo_provider" in err
    assert "always_no" in err  # lista los válidos


def test_all_adapters_includes_claude_code():
    names = [a.name for a in registry.ALL_ADAPTERS]
    assert "claude_code" in names


class _Raises:
    name = "raises"
    def detect(self, project_root): raise OSError("permission denied")
    def target_paths(self, project_root, skill_ids): return {}
    def render(self, skill_id, content_md): return content_md


def test_detect_skips_adapter_that_raises_and_keeps_others(tmp_path: Path, capsys):
    found = registry.detect(tmp_path, adapters=[_Raises(), _AlwaysYes()])
    assert [a.name for a in found] == ["always_yes"]
    assert "raises" in capsys.readouterr().err


from factorysoftware.adapters.copilot import CopilotAdapter


def test_copilot_detect_true_with_dot_github(tmp_path: Path):
    (tmp_path / ".github").mkdir()
    assert CopilotAdapter().detect(tmp_path) is True


def test_copilot_detect_false_when_absent(tmp_path: Path):
    assert CopilotAdapter().detect(tmp_path) is False


def test_copilot_target_paths_all_same_file(tmp_path: Path):
    paths = CopilotAdapter().target_paths(tmp_path, ["requirements-prd", "requirements-flujo"])
    assert paths["requirements-prd"] == paths["requirements-flujo"] == tmp_path / ".github" / "copilot-instructions.md"


def test_copilot_render_adds_heading():
    rendered = CopilotAdapter().render("requirements-prd", "Hacé el PRD.")
    assert rendered.startswith("## requirements-prd")
    assert "Hacé el PRD." in rendered


from factorysoftware.adapters.codex import CodexAdapter
from factorysoftware.adapters.opencode import OpenCodeAdapter


def test_codex_detect_false_without_marker(tmp_path: Path):
    assert CodexAdapter().detect(tmp_path) is False


def test_codex_detect_true_with_codex_marker(tmp_path: Path):
    (tmp_path / ".codex").mkdir()
    assert CodexAdapter().detect(tmp_path) is True


def test_codex_target_paths_all_same_agents_md(tmp_path: Path):
    paths = CodexAdapter().target_paths(tmp_path, ["a", "b"])
    assert paths["a"] == paths["b"] == tmp_path / "AGENTS.md"


def test_codex_render_is_plain_no_frontmatter():
    rendered = CodexAdapter().render("requirements-prd", "Hacé el PRD.")
    assert not rendered.startswith("---")
    assert "Hacé el PRD." in rendered


def test_opencode_target_paths_same_as_codex(tmp_path: Path):
    paths = OpenCodeAdapter().target_paths(tmp_path, ["a"])
    assert paths["a"] == tmp_path / "AGENTS.md"


def test_opencode_detect_false_without_marker(tmp_path: Path):
    assert OpenCodeAdapter().detect(tmp_path) is False


from factorysoftware.adapters.antigravity import AntigravityAdapter


def test_antigravity_detect_true_with_dot_agents(tmp_path: Path):
    (tmp_path / ".agents").mkdir()
    assert AntigravityAdapter().detect(tmp_path) is True


def test_antigravity_detect_false_when_absent(tmp_path: Path):
    assert AntigravityAdapter().detect(tmp_path) is False


def test_antigravity_target_paths_mirrors_claude_code_layout(tmp_path: Path):
    paths = AntigravityAdapter().target_paths(tmp_path, ["requirements-prd"])
    assert paths["requirements-prd"] == tmp_path / ".agents" / "skills" / "requirements-prd" / "SKILL.md"


def test_antigravity_render_adds_frontmatter():
    rendered = AntigravityAdapter().render("requirements-prd", "Hacé el PRD.")
    assert "name: requirements-prd" in rendered
    assert "Hacé el PRD." in rendered


def test_antigravity_install_gitflow_hook_writes_hooks_json(tmp_path: Path):
    written = AntigravityAdapter().install_gitflow_hook(tmp_path)
    hooks_path = tmp_path / ".agents" / "hooks.json"
    assert hooks_path in written
    assert hooks_path.exists()


def test_antigravity_install_gitflow_hook_writes_guard_script(tmp_path: Path):
    written = AntigravityAdapter().install_gitflow_hook(tmp_path)
    guard = tmp_path / ".agents" / "gitflow-guard.sh"
    assert guard in written
    assert guard.exists()
    assert "git commit" in guard.read_text(encoding="utf-8")
    assert "main" in guard.read_text(encoding="utf-8")


def test_antigravity_install_gitflow_hook_registers_pretooluse_run_command(tmp_path: Path):
    # Schema verified against official docs (antigravity.google/docs/hooks):
    # {"<hook-name>": {"PreToolUse": [{"matcher": "run_command", "hooks": [{"type": "command", "command": ...}]}]}}
    AntigravityAdapter().install_gitflow_hook(tmp_path)
    hooks_path = tmp_path / ".agents" / "hooks.json"
    hooks_config = json.loads(hooks_path.read_text(encoding="utf-8"))
    pretooluse = hooks_config["gitflow-guard"]["PreToolUse"]
    assert any(entry["matcher"] == "run_command" for entry in pretooluse)
    entry = next(e for e in pretooluse if e["matcher"] == "run_command")
    assert isinstance(entry["hooks"], list)
    assert len(entry["hooks"]) > 0
    hook = entry["hooks"][0]
    assert hook["type"] == "command"
    assert "gitflow-guard.sh" in hook["command"]


def test_antigravity_install_gitflow_hook_merges_existing_hooks_json(tmp_path: Path):
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".agents" / "hooks.json").write_text(
        json.dumps({"other-hook": {"PostToolUse": []}}), encoding="utf-8"
    )
    AntigravityAdapter().install_gitflow_hook(tmp_path)
    hooks_config = json.loads((tmp_path / ".agents" / "hooks.json").read_text(encoding="utf-8"))
    assert "other-hook" in hooks_config
    assert "gitflow-guard" in hooks_config


def test_antigravity_install_gitflow_hook_raises_on_malformed_json(tmp_path: Path):
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".agents" / "hooks.json").write_text("{ invalid json", encoding="utf-8")
    try:
        AntigravityAdapter().install_gitflow_hook(tmp_path)
        assert False, "Expected ValueError to be raised"
    except ValueError as e:
        assert "malformed JSON" in str(e)
        assert "hooks.json" in str(e)
        assert "fix or remove" in str(e)


def test_antigravity_install_gitflow_hook_is_idempotent(tmp_path: Path):
    adapter = AntigravityAdapter()
    adapter.install_gitflow_hook(tmp_path)
    hooks_path = tmp_path / ".agents" / "hooks.json"
    first = json.loads(hooks_path.read_text(encoding="utf-8"))
    first_count = len(first["gitflow-guard"]["PreToolUse"])

    adapter.install_gitflow_hook(tmp_path)
    second = json.loads(hooks_path.read_text(encoding="utf-8"))
    second_count = len(second["gitflow-guard"]["PreToolUse"])

    assert first_count == second_count == 1
