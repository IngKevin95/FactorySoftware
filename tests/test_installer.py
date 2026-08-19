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


from factorysoftware.installer import install_all
from factorysoftware.state import read_manifest

_FIXTURE_PHASE = """\
---
id: requirements
steps:
  - id: prd
    depende_de: []
---
Preámbulo.

## Paso: prd

Hacé el PRD.
"""


def test_install_all_writes_files_and_manifest(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")

    manifest = install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    assert manifest.providers == ["multi"]
    assert len(manifest.files) == 2  # requirements-prd, requirements-flujo
    assert read_manifest(tmp_path) == manifest
    assert (tmp_path / "requirements-prd.md").exists()
    assert (tmp_path / "requirements-flujo.md").exists()


class _UnwritableAdapter:
    name = "unwritable"
    def detect(self, project_root): return True
    def target_paths(self, project_root, skill_ids):
        return {sid: project_root / "nope" / f"{sid}.md" for sid in skill_ids}
    def render(self, skill_id, content_md):
        raise OSError("simulated permission denied")


def test_install_all_skips_adapter_that_fails_to_write(tmp_path: Path, capsys):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")

    manifest = install_all(tmp_path, content_dir, adapters=[_UnwritableAdapter(), _MultiFileAdapter()])

    assert manifest.providers == ["unwritable", "multi"]
    assert (tmp_path / "requirements-prd.md").exists()  # multi still wrote its files
    assert "unwritable" in capsys.readouterr().err
