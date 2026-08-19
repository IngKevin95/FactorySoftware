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
