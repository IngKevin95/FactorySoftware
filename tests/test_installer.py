import json
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


_FIXTURE_PHASE_2 = """\
---
id: architecture
steps:
  - id: adrs
    depende_de: []
---
Preámbulo de arquitectura.

## Paso: adrs

Escribí los ADRs.
"""


def _make_two_phase_content_dir(tmp_path: Path) -> Path:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    (content_dir / "architecture.md").write_text(_FIXTURE_PHASE_2, encoding="utf-8")
    return content_dir


def test_install_all_merges_every_phase_into_one_single_file_target(tmp_path: Path):
    content_dir = _make_two_phase_content_dir(tmp_path)

    manifest = install_all(tmp_path, content_dir, adapters=[_SingleFileAdapter()])

    combined = (tmp_path / "combined.md").read_text(encoding="utf-8")
    assert "## requirements-prd" in combined
    assert "## architecture-adrs" in combined
    assert "Hacé el PRD." in combined
    assert "Escribí los ADRs." in combined

    entries = [f for f in manifest.files if f.path == "combined.md"]
    assert len(entries) == 1
    assert len(manifest.files) == 1
    assert entries[0].hash == compute_hash(combined)


def test_update_all_after_install_does_not_warn_about_single_file_adapter(tmp_path: Path):
    content_dir = _make_two_phase_content_dir(tmp_path)
    install_all(tmp_path, content_dir, adapters=[_SingleFileAdapter()])

    manifest, warnings = update_all(tmp_path, content_dir, adapters=[_SingleFileAdapter()])

    assert warnings == []
    combined = (tmp_path / "combined.md").read_text(encoding="utf-8")
    assert "## requirements-prd" in combined
    assert "## architecture-adrs" in combined
    assert len(manifest.files) == 1


class _SingleFileAdapterB(_SingleFileAdapter):
    name = "single_b"


def test_install_all_dedupes_manifest_entries_sharing_one_path(tmp_path: Path):
    content_dir = _make_two_phase_content_dir(tmp_path)

    manifest = install_all(
        tmp_path, content_dir, adapters=[_SingleFileAdapter(), _SingleFileAdapterB()]
    )

    assert [f.path for f in manifest.files] == ["combined.md"]


_MALFORMED_PHASE = "# Un README suelto sin frontmatter.\n"


def test_install_all_skips_malformed_content_file_and_keeps_going(tmp_path: Path, capsys):
    content_dir = _make_two_phase_content_dir(tmp_path)
    (content_dir / "README.md").write_text(_MALFORMED_PHASE, encoding="utf-8")

    manifest = install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    assert "README.md" in capsys.readouterr().err
    assert (tmp_path / "requirements-prd.md").exists()
    assert (tmp_path / "architecture-adrs.md").exists()
    assert len(manifest.files) == 4  # prd, requirements-flujo, adrs, architecture-flujo


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


from factorysoftware.installer import update_all


def test_update_all_overwrites_untouched_files(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    original_manifest = install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    (content_dir / "requirements.md").write_text(
        _FIXTURE_PHASE.replace("Hacé el PRD.", "Hacé el PRD actualizado."), encoding="utf-8"
    )
    manifest, warnings = update_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    assert "Hacé el PRD actualizado." in (tmp_path / "requirements-prd.md").read_text(encoding="utf-8")
    assert warnings == []

    # Verify manifest has updated hash for the file
    original_prd_entry = next((f for f in original_manifest.files if "requirements-prd" in f.path), None)
    updated_prd_entry = next((f for f in manifest.files if "requirements-prd" in f.path), None)
    assert original_prd_entry is not None
    assert updated_prd_entry is not None
    assert original_prd_entry.hash != updated_prd_entry.hash


def test_update_all_skips_user_edited_files(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    original_manifest = install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    (tmp_path / "requirements-prd.md").write_text("edición manual del usuario", encoding="utf-8")
    (content_dir / "requirements.md").write_text(
        _FIXTURE_PHASE.replace("Hacé el PRD.", "Hacé el PRD actualizado."), encoding="utf-8"
    )
    manifest, warnings = update_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    assert (tmp_path / "requirements-prd.md").read_text(encoding="utf-8") == "edición manual del usuario"
    assert any("requirements-prd" in w for w in warnings)

    # Verify manifest entry was preserved exactly (same hash and skill_id)
    original_prd_entry = next((f for f in original_manifest.files if "requirements-prd" in f.path), None)
    updated_prd_entry = next((f for f in manifest.files if "requirements-prd" in f.path), None)
    assert original_prd_entry is not None
    assert updated_prd_entry is not None
    assert original_prd_entry.hash == updated_prd_entry.hash
    assert original_prd_entry.skill_id == updated_prd_entry.skill_id


from factorysoftware.installer import uninstall_all
from factorysoftware.state import read_manifest as _read_manifest_for_test


def test_uninstall_all_removes_manifest_files(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])

    warnings = uninstall_all(tmp_path)

    assert warnings == []
    assert not (tmp_path / "requirements-prd.md").exists()
    assert not (tmp_path / "requirements-flujo.md").exists()
    assert _read_manifest_for_test(tmp_path) is None


def test_uninstall_all_skips_user_edited_files(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    install_all(tmp_path, content_dir, adapters=[_MultiFileAdapter()])
    (tmp_path / "requirements-prd.md").write_text("edición manual", encoding="utf-8")

    warnings = uninstall_all(tmp_path)

    assert (tmp_path / "requirements-prd.md").exists()
    assert any("requirements-prd" in w for w in warnings)


from factorysoftware.adapters.claude_code import ClaudeCodeAdapter


def test_install_all_installs_and_records_gitflow_hook(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    (tmp_path / ".claude").mkdir()

    manifest = install_all(tmp_path, content_dir, adapters=[ClaudeCodeAdapter()])

    guard = tmp_path / ".claude" / "hooks" / "gitflow-guard.sh"
    settings = tmp_path / ".claude" / "settings.json"
    assert guard.exists()
    assert settings.exists()

    recorded = {f.path for f in manifest.files}
    assert str(Path(".claude") / "hooks" / "gitflow-guard.sh") in recorded
    assert str(Path(".claude") / "settings.json") in recorded


def test_update_all_keeps_gitflow_hook_tracked(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    (tmp_path / ".claude").mkdir()
    install_all(tmp_path, content_dir, adapters=[ClaudeCodeAdapter()])

    manifest, warnings = update_all(tmp_path, content_dir, adapters=[ClaudeCodeAdapter()])

    assert warnings == []
    assert str(Path(".claude") / "settings.json") in {f.path for f in manifest.files}


def _install_with_claude_code(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    (tmp_path / ".claude").mkdir()
    install_all(tmp_path, content_dir, adapters=[ClaudeCodeAdapter()])


def test_uninstall_all_keeps_user_settings_that_predate_the_install(tmp_path: Path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"userSetting": True}), encoding="utf-8")

    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    install_all(tmp_path, content_dir, adapters=[ClaudeCodeAdapter()])
    assert "hooks" in json.loads(settings.read_text(encoding="utf-8"))

    warnings = uninstall_all(tmp_path)

    assert warnings == []
    assert settings.exists()
    remaining = json.loads(settings.read_text(encoding="utf-8"))
    assert remaining == {"userSetting": True}


def test_uninstall_all_removes_settings_file_when_only_the_hook_was_in_it(tmp_path: Path):
    _install_with_claude_code(tmp_path)

    warnings = uninstall_all(tmp_path)

    assert warnings == []
    assert not (tmp_path / ".claude" / "settings.json").exists()


def test_uninstall_all_removes_gitflow_guard_script(tmp_path: Path):
    _install_with_claude_code(tmp_path)
    guard = tmp_path / ".claude" / "hooks" / "gitflow-guard.sh"
    assert guard.exists()

    warnings = uninstall_all(tmp_path)

    assert warnings == []
    assert not guard.exists()
    assert not guard.parent.exists()


def test_update_all_warns_instead_of_crashing_on_malformed_settings(tmp_path: Path, capsys):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{ invalid json", encoding="utf-8")

    install_all(tmp_path, content_dir, adapters=[ClaudeCodeAdapter()])
    assert "malformed JSON" in capsys.readouterr().err

    manifest, warnings = update_all(tmp_path, content_dir, adapters=[ClaudeCodeAdapter()])

    err = capsys.readouterr().err
    assert "claude_code" in err
    assert "malformed JSON" in err
    assert manifest.providers == ["claude_code"]
    # el archivo roto del usuario queda como estaba, no lo pisa nadie
    assert (tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8") == "{ invalid json"


def test_uninstall_all_preserves_provider_marker_directory(tmp_path: Path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    (tmp_path / ".claude").mkdir()
    install_all(tmp_path, content_dir, adapters=[ClaudeCodeAdapter()])

    warnings = uninstall_all(tmp_path)

    assert warnings == []
    assert not (tmp_path / ".claude" / "skills" / "requirements-prd").exists()
    # .claude lo creó el usuario y es lo que hace detectable al proveedor:
    # uninstall no puede borrarlo aunque quede vacío.
    assert (tmp_path / ".claude").is_dir()
