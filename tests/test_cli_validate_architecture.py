import pytest
from pathlib import Path
from factorysoftware.cli import main

def test_cli_validate_architecture(tmp_path, capsys):
    code = main(["validate", "architecture", "--project-root", str(tmp_path)])
    assert code == 0

def test_cli_validate_architecture_error(tmp_path, capsys):
    docs_dir = tmp_path / "docs"
    req_dir = docs_dir / "requirements"
    (req_dir / "stories").mkdir(parents=True)
    (req_dir / "stories" / "HU-1.1.md").write_text("---\nid: HU-1.1\nestado: draft\n---\nanexo endpoint\n", encoding="utf-8")
    
    code = main(["validate", "architecture", "--project-root", str(tmp_path)])
    assert code == 1
    err = capsys.readouterr().err
    assert "Check 1: HU 'HU-1.1' requests an endpoint but no API-N.md implements it" in err
