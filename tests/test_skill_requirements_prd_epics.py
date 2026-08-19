"""
Contract tests: verify the expected output format of requirements-prd and
requirements-epics deliverables. Uses fixtures that simulate post-skill execution.
"""
from __future__ import annotations
import json
from pathlib import Path
import yaml
import pytest


def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"


# --- PRD contract ---

@pytest.fixture
def prd_output(tmp_path: Path) -> Path:
    prd = tmp_path / "docs" / "requirements" / "PRD.md"
    prd.parent.mkdir(parents=True)
    prd.write_text(
        "# PRD\n\n"
        "## Problema\nAlgo.\n\n"
        "## Objetivo de negocio\nUna frase.\n\n"
        "## Alcance\n### Que entra\n- X\n### Que no entra\n- Y\n\n"
        "## Metricas de exito\n- M1\n\n"
        "## Stakeholders\n- S1\n\n"
        "## Restricciones\n- R1\n\n"
        "## Supuestos\n- A1\n",
        encoding="utf-8",
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "step_complete", "step": "prd",
                    "output_files": ["docs/requirements/PRD.md"]}) + "\n"
    )
    return tmp_path


def test_prd_file_exists(prd_output):
    assert (prd_output / "docs" / "requirements" / "PRD.md").exists()


def test_prd_log_step_complete(prd_output):
    events = [json.loads(l) for l in
              (prd_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events if e.get("step") == "prd" and e.get("type") == "step_complete"]
    assert len(done) == 1
    assert "docs/requirements/PRD.md" in done[0]["output_files"]


def test_prd_required_sections(prd_output):
    text = (prd_output / "docs" / "requirements" / "PRD.md").read_text()
    for s in ["Problema", "Alcance", "Metricas", "Stakeholders"]:
        assert s in text, f"PRD missing section containing: {s}"


# --- Epics contract ---

@pytest.fixture
def epics_output(tmp_path: Path) -> Path:
    epic = tmp_path / "docs" / "requirements" / "epics" / "EPIC-1.md"
    epic.parent.mkdir(parents=True)
    epic.write_text(
        _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "Obj1"},
            "## Meta de negocio\nAlgo.\n\n## HUs\n- HU-1.1\n"),
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "advisor_note", "category": "sugerencia_transversal",
                    "step": "epics", "suggestions": ["autenticacion"], "accepted": []}) + "\n" +
        json.dumps({"type": "step_complete", "step": "epics",
                    "output_files": ["docs/requirements/epics/EPIC-1.md"]}) + "\n"
    )
    return tmp_path


def test_epic_file_exists(epics_output):
    assert (epics_output / "docs" / "requirements" / "epics" / "EPIC-1.md").exists()


def test_epic_frontmatter_fields(epics_output):
    text = (epics_output / "docs" / "requirements" / "epics" / "EPIC-1.md").read_text()
    fm = yaml.safe_load(text.split("---")[1])
    assert fm["id"] == "EPIC-1"
    assert fm["estado"] in ("draft", "validada")
    assert "objetivo_prd" in fm


def test_epics_advisor_note_logged(epics_output):
    events = [json.loads(l) for l in
              (epics_output / ".factory" / "log.jsonl").read_text().splitlines()]
    notes = [e for e in events
             if e.get("type") == "advisor_note"
             and e.get("category") == "sugerencia_transversal"]
    assert len(notes) >= 1


def test_epics_step_complete_logged(epics_output):
    events = [json.loads(l) for l in
              (epics_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events if e.get("step") == "epics" and e.get("type") == "step_complete"]
    assert len(done) == 1
