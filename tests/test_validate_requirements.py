from __future__ import annotations
import json
from pathlib import Path
import pytest
import yaml
from factorysoftware.requirements.validator import validate_requirements


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"


def _log(log_path: Path, event: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


@pytest.fixture
def docs(tmp_path: Path) -> Path:
    return tmp_path / "docs" / "requirements"


@pytest.fixture
def log_path(tmp_path: Path) -> Path:
    return tmp_path / ".factory" / "log.jsonl"


# --- Check 1: every epic referenced by traceability row has a file in epics/ ---

def test_check1_missing_epic_file(docs, log_path):
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []}))
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n"
           "|----|-------|--------|----|----|\n"
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("EPIC-1" in e and "epics/" in e for e in errors)


# --- Check 2: HU listed in epic has file; HU file is listed in epic ---

def test_check2_hu_listed_in_epic_but_no_file(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n- HU-1.2\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.2" in e for e in errors)


def test_check2_hu_file_not_listed_in_any_epic(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []}))
    _write(docs / "stories" / "HU-1.2.md",
           _fm({"id": "HU-1.2", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "media", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.2" in e for e in errors)


# --- Check 3: depende_de ids exist + no circular deps ---

def test_check3_missing_dependency(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": ["HU-1.2"]}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.2" in e and "depende_de" in e for e in errors)


def test_check3_circular_dependency(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n- HU-1.2\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": ["HU-1.2"]}))
    _write(docs / "stories" / "HU-1.2.md",
           _fm({"id": "HU-1.2", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": ["HU-1.1"]}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("circular" in e.lower() for e in errors)


# --- Check 4: every HU has at least one Given/When/Then ---

def test_check4_no_gwt(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "Como usuario quiero algo para algo.\n"))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.1" in e and ("Given" in e or "criterio" in e.lower()) for e in errors)


# --- Check 5: traceability has exactly one row per non-retired HU ---

def test_check5_missing_row(docs, log_path):
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n|----|-------|--------|----|----|\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.1" in e and "traceability" in e.lower() for e in errors)


def test_check5_orphan_row(docs, log_path):
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
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n"
           "| HU-9.9 | EPIC-9 | draft | _p_ | _p_ |\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-9.9" in e for e in errors)


# --- Check 6: advisor_note sugerencia_transversal in log ---

def test_check6_missing_advisor_note(docs, log_path):
    _log(log_path, {"type": "step_complete", "step": "epics"})
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("sugerencia_transversal" in e or "advisor_note" in e for e in errors)


def test_check6_passes_when_note_present(docs, log_path):
    _log(log_path, {"type": "advisor_note",
                    "category": "sugerencia_transversal", "step": "epics"})
    # minimal valid structure so other checks pass too
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
    errors = validate_requirements(docs.parent.parent, log_path)
    assert not any("sugerencia_transversal" in e for e in errors)


# --- Check 7: every hu id in FLUJO-N.md exists as a file ---

def test_check7_flujo_references_missing_hu(docs, log_path):
    _write(docs / "flujos" / "FLUJO-1.md",
           _fm({"id": "FLUJO-1", "estado": "draft", "hu": ["HU-1.1", "HU-9.9"]}))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-9.9" in e and "FLUJO-1" in e for e in errors)


def test_check7_retired_hu_is_acceptable(docs, log_path):
    _write(docs / "flujos" / "FLUJO-1.md",
           _fm({"id": "FLUJO-1", "estado": "draft", "hu": ["HU-1.1"]}))
    _write(docs / "stories" / "retiradas" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "retirada",
                "prioridad": "alta", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert not any("HU-1.1" in e and "FLUJO-1" in e for e in errors)


# --- Happy path: fully valid minimal set ---

def test_happy_path(docs, log_path):
    _log(log_path, {"type": "advisor_note",
                    "category": "sugerencia_transversal", "step": "epics"})
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
    errors = validate_requirements(docs.parent.parent, log_path)
    assert errors == []
