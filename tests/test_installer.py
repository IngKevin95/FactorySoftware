from pathlib import Path

from factorysoftware.installer import write_skills
from factorysoftware.state import compute_hash


class _MultiFileAdapter:
    name = "multi"
    def detect(self, project_root): return True
    def target_paths(self, project_root, skill_ids):
        return {sid: project_root / f"{sid}.md" for sid in skill_ids}
    def render(self, skill_id, content_md):
        return f"# {skill_id}\n{content_md}"


class _SingleFileAdapter:
    name = "single"
    def detect(self, project_root): return True
    def target_paths(self, project_root, skill_ids):
        target = project_root / "combined.md"
        return {sid: target for sid in skill_ids}
    def render(self, skill_id, content_md):
        return f"## {skill_id}\n{content_md}"


def test_write_skills_one_file_per_skill(tmp_path: Path):
    files = write_skills(tmp_path, _MultiFileAdapter(), {"a": "content a", "b": "content b"})
    assert (tmp_path / "a.md").read_text(encoding="utf-8") == "# a\ncontent a"
    assert (tmp_path / "b.md").read_text(encoding="utf-8") == "# b\ncontent b"
    assert len(files) == 2
    assert {f.skill_id for f in files} == {"a", "b"}


def test_write_skills_groups_single_file_adapter(tmp_path: Path):
    files = write_skills(tmp_path, _SingleFileAdapter(), {"a": "content a", "b": "content b"})
    combined = tmp_path / "combined.md"
    text = combined.read_text(encoding="utf-8")
    assert "## a\ncontent a" in text
    assert "## b\ncontent b" in text
    assert text.index("## a") < text.index("## b")
    assert len(files) == 1
    assert files[0].skill_id == "a,b"
    assert files[0].hash == compute_hash(text)
