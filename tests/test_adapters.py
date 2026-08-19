from pathlib import Path

from factorysoftware.adapters.base import ProviderAdapter


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
