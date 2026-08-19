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


def test_install_gitflow_hook_merges_existing_settings(tmp_path: Path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        json.dumps({"otherSetting": True}), encoding="utf-8"
    )
    ClaudeCodeAdapter().install_gitflow_hook(tmp_path)
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert settings["otherSetting"] is True
    assert "hooks" in settings
