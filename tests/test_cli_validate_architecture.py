import pytest
from pathlib import Path
from factorysoftware.cli import main

def test_cli_validate_architecture(tmp_path, capsys):
    code = main(["validate", "architecture", "--project-root", str(tmp_path)])
    assert code == 0
