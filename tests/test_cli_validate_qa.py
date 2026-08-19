import pytest
from factorysoftware.cli import main

def test_cli_validate_qa():
    try:
        exit_code = main(["validate", "qa", "--project-root", "."])
    except SystemExit as e:
        exit_code = e.code
    
    assert exit_code == 0
