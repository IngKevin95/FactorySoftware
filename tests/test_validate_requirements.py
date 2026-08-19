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


# --- Finding 1: Check 1 validates traceability row's epic column directly ---

def test_check1_validates_traceability_epic_not_story_file(docs, log_path):
    """Traceability row references non-existent epic even if story file's epica is valid."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    # Traceability row says EPIC-9 (doesn't exist), but story file says EPIC-1
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n"
           "|----|-------|--------|----|----|\n"
           "| HU-1.1 | EPIC-9 | draft | _p_ | _p_ |\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    # Must flag EPIC-9 from traceability row, not trust story file's EPIC-1
    assert any("EPIC-9" in e and "traceability" in e.lower() for e in errors)


# --- Finding 2: Check 5 detects duplicate traceability rows ---

def test_check5_detects_duplicate_rows(docs, log_path):
    """Traceability with two rows for same HU should be flagged."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    # Two rows for HU-1.1
    _write(docs / "traceability.md",
           "| HU | Epica | Estado | CP | CA |\n"
           "|----|-------|--------|----|----|\n"
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n"
           "| HU-1.1 | EPIC-1 | draft | _p_ | _p_ |\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.1" in e and "2 rows" in e for e in errors)


# --- Finding 3: Check 8 detects empty/missing epica ---

def test_check8_missing_epica(docs, log_path):
    """HU with missing epica field should be flagged."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.1" in e and "epica" in e.lower() for e in errors)


def test_check8_empty_epica(docs, log_path):
    """HU with empty epica field should be flagged."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "", "estado": "draft",
                "prioridad": "alta", "depende_de": []},
               "**Given** X **When** Y **Then** Z"))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.1" in e and "epica" in e.lower() for e in errors)


# --- Finding 4: Graceful error handling for malformed frontmatter ---

def test_malformed_frontmatter_missing_closing_delimiter(docs, log_path):
    """File with missing closing --- should return error, not crash."""
    _write(docs / "epics" / "EPIC-1.md",
           "---\nid: EPIC-1\nestado: draft\n")  # Missing closing ---
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("Parse error" in e and "EPIC-1" in e for e in errors)


def test_malformed_frontmatter_invalid_yaml(docs, log_path):
    """File with invalid YAML should return error, not crash."""
    _write(docs / "stories" / "HU-1.1.md",
           "---\nid: HU-1.1\ninvalid: [unclosed bracket\n---\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("Parse error" in e and "HU-1.1" in e for e in errors)


# --- Fix 2: validate_requirements must never raise on malformed input ---

def test_scalar_frontmatter_returns_errors_not_raise(docs, log_path):
    """Frontmatter that is a bare YAML scalar string must not crash with AttributeError."""
    _write(docs / "stories" / "HU-1.1.md", "---\njust a string\n---\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)
    assert any("Parse error" in e for e in errors)


def test_list_frontmatter_returns_errors_not_raise(docs, log_path):
    """Frontmatter that is a bare YAML list must not crash with AttributeError."""
    _write(docs / "stories" / "HU-1.1.md", "---\n- a\n- b\n---\n")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)
    assert any("Parse error" in e for e in errors)


def test_depende_de_as_int_returns_errors_not_raise(docs, log_path):
    """depende_de: 5 (int, not list) must not crash with TypeError."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": 5},
               "**Given** X **When** Y **Then** Z"))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)


def test_flujo_hu_as_int_returns_errors_not_raise(docs, log_path):
    """hu: 7 (int, not list) in a FLUJO frontmatter must not crash with TypeError."""
    _write(docs / "flujos" / "FLUJO-1.md",
           _fm({"id": "FLUJO-1", "estado": "draft", "hu": 7}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)


def test_non_dict_log_line_returns_errors_not_raise(docs, log_path):
    """A log line that is valid JSON but not an object must not crash with AttributeError."""
    _log(log_path, 123)
    _log(log_path, "hello")
    errors = validate_requirements(docs.parent.parent, log_path)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)


def test_depende_de_as_scalar_string_is_not_iterated_char_by_char(docs, log_path):
    """depende_de: HU-1.2 (a scalar string, not a list) must not be iterated
    character-by-character - it must be treated as no dependencies, not as
    bogus per-character deps like 'H', 'U', '-'."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": "HU-1.2"},
               "**Given** X **When** Y **Then** Z"))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)
    bogus_chars = {"H", "U", "-", "1", ".", "2"}
    for e in errors:
        if "depende_de" in e:
            for ch in bogus_chars:
                assert f"'{ch}'" not in e, f"bogus per-character dep found in: {e}"


# --- Fix 4: retired HUs referenced from epic lists / depende_de are accepted ---

def test_check2a_epic_listing_retired_hu_is_acceptable(docs, log_path):
    """An epic listing a retired HU (moved to stories/retiradas/) must not
    trigger Check 2's 'no file in stories/' error."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "retiradas" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "retirada",
                "prioridad": "alta", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert not any("HU-1.1" in e and "no file in stories/" in e for e in errors)


def test_check3_depende_de_referencing_retired_hu_is_acceptable(docs, log_path):
    """An active HU's depende_de referencing a retired HU must not trigger
    Check 3's 'does not exist' error."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": ["HU-1.2"]},
               "**Given** X **When** Y **Then** Z"))
    _write(docs / "stories" / "retiradas" / "HU-1.2.md",
           _fm({"id": "HU-1.2", "epica": "EPIC-1", "estado": "retirada",
                "prioridad": "alta", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert not any("HU-1.2" in e and "depende_de" in e and "does not exist" in e for e in errors)


def test_check2a_still_fails_when_hu_missing_everywhere(docs, log_path):
    """Sanity: Check 2 must still fire when the referenced HU has no file at
    all (active or retired) - only the retired case changes behavior."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n- HU-1.2\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": []}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.2" in e for e in errors)


def test_directory_matching_hu_glob_pattern_is_skipped_not_raise(docs, log_path):
    """A directory that happens to match the HU glob pattern (e.g.
    stories/HU-1.1.md/ as a directory) must be skipped, not crash with
    IsADirectoryError/PermissionError when .read_text() is attempted on it."""
    (docs / "stories" / "HU-1.1.md").mkdir(parents=True)
    errors = validate_requirements(docs.parent.parent, log_path)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)


def test_check3_still_fails_when_dependency_missing_everywhere(docs, log_path):
    """Sanity: Check 3 must still fire when depende_de targets an id that
    does not exist as a file anywhere - only the retired case changes
    behavior."""
    _write(docs / "epics" / "EPIC-1.md",
           _fm({"id": "EPIC-1", "estado": "draft", "objetivo_prd": "O1"},
               "## HUs\n- HU-1.1\n"))
    _write(docs / "stories" / "HU-1.1.md",
           _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
                "prioridad": "alta", "depende_de": ["HU-1.2"]}))
    errors = validate_requirements(docs.parent.parent, log_path)
    assert any("HU-1.2" in e and "depende_de" in e for e in errors)
