from __future__ import annotations
import json
from pathlib import Path
import yaml
import pytest
from factorysoftware.cli import main


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"


def test_validate_requirements_clean(tmp_path, capsys):
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir(parents=True)
    log.write_text(
        json.dumps({"type": "advisor_note",
                    "category": "sugerencia_transversal", "step": "epics"}) + "\n"
    )
    docs = tmp_path / "docs" / "requirements"
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n"
           "|----|-------|--------|----|----|\n"
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n")

    code = main(["validate", "requirements",
                 "--project-root", str(tmp_path),
                 "--log", str(log)])
    assert code == 0
    assert capsys.readouterr().out.strip() == ""


def test_validate_requirements_reports_errors(tmp_path, capsys):
    # empty log -> check 6 fails
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir(parents=True)
    log.write_text("")

    code = main(["validate", "requirements",
                 "--project-root", str(tmp_path),
                 "--log", str(log)])
    assert code == 1
    out = capsys.readouterr().out
    assert "sugerencia_transversal" in out
