import pytest
from pathlib import Path
from factorysoftware.qa.validator import validate_qa

def test_validate_qa_clean(tmp_path: Path):
    docs = tmp_path / "docs" / "qa"
    docs.mkdir(parents=True, exist_ok=True)
    assert validate_qa(tmp_path) == []
