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
