from pathlib import Path
from factorysoftware.cli import main

def test_validate_construction(tmp_path: Path):
    assert main(["validate", "construction", "--project-root", str(tmp_path)]) == 0

def test_audit_triage(tmp_path: Path):
    assert main(["audit-triage", "--epic", "EPIC-1", "--project-root", str(tmp_path)]) == 0
