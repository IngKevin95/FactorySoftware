import shutil
from pathlib import Path

from factorysoftware.cli import main


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


def _make_content_dir(tmp_path: Path) -> Path:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "requirements.md").write_text(_FIXTURE_PHASE, encoding="utf-8")
    return content_dir


def test_init_with_no_detected_provider_and_no_override_errors(tmp_path: Path, capsys):
    content_dir = _make_content_dir(tmp_path)
    code = main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir)])
    assert code != 0
    assert "ningún proveedor" in capsys.readouterr().err.lower()


def test_init_with_providers_override_installs(tmp_path: Path):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    code = main([
        "init", "--project-root", str(tmp_path), "--content-dir", str(content_dir),
        "--providers", "claude_code",
    ])
    assert code == 0
    assert (tmp_path / ".claude" / "skills" / "requirements-prd" / "SKILL.md").exists()
    assert (tmp_path / ".factory" / "manifest.json").exists()


def test_init_twice_behaves_like_update(tmp_path: Path):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir), "--providers", "claude_code"])
    code = main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir), "--providers", "claude_code"])
    assert code == 0


def test_update_without_prior_init_errors(tmp_path: Path, capsys):
    content_dir = _make_content_dir(tmp_path)
    code = main(["update", "--project-root", str(tmp_path), "--content-dir", str(content_dir)])
    assert code != 0
    assert "init" in capsys.readouterr().err.lower()


def test_update_falls_back_to_manifest_providers_when_nothing_detected(tmp_path: Path):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    init_code = main([
        "init", "--project-root", str(tmp_path), "--content-dir", str(content_dir),
        "--providers", "claude_code",
    ])
    assert init_code == 0
    skill_path = tmp_path / ".claude" / "skills" / "requirements-prd" / "SKILL.md"
    assert skill_path.exists()

    # Remove the marker directory the adapter's detect() relies on, so a
    # plain registry.detect() on the next call finds nothing.
    shutil.rmtree(tmp_path / ".claude")

    code = main(["update", "--project-root", str(tmp_path), "--content-dir", str(content_dir)])
    assert code == 0
    # update_all recreated the file using the provider recorded in the
    # manifest, proving the detect-nothing fallback to manifest.providers
    # kicked in rather than silently doing nothing.
    assert skill_path.exists()


def test_update_prints_warning_for_hand_edited_file(tmp_path: Path, capsys):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    init_code = main([
        "init", "--project-root", str(tmp_path), "--content-dir", str(content_dir),
        "--providers", "claude_code",
    ])
    assert init_code == 0
    skill_path = tmp_path / ".claude" / "skills" / "requirements-prd" / "SKILL.md"
    skill_path.write_text("edited by hand, not by factory", encoding="utf-8")

    code = main(["update", "--project-root", str(tmp_path), "--content-dir", str(content_dir)])
    assert code == 0
    err = capsys.readouterr().err
    assert "editado a mano" in err.lower()
    # The hand-edited content must not have been overwritten.
    assert skill_path.read_text(encoding="utf-8") == "edited by hand, not by factory"


def test_uninstall_without_prior_init_errors(tmp_path: Path, capsys):
    code = main(["uninstall", "--project-root", str(tmp_path)])
    assert code != 0
    assert "init" in capsys.readouterr().err.lower()


def test_uninstall_after_init_removes_files(tmp_path: Path):
    content_dir = _make_content_dir(tmp_path)
    (tmp_path / ".claude").mkdir()
    main(["init", "--project-root", str(tmp_path), "--content-dir", str(content_dir), "--providers", "claude_code"])
    code = main(["uninstall", "--project-root", str(tmp_path)])
    assert code == 0
    assert not (tmp_path / ".claude" / "skills" / "requirements-prd").exists()
