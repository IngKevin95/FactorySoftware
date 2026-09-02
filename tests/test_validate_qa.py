import json
from pathlib import Path
import pytest
from factorysoftware.qa.validator import validate_qa

def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _traceability(rows: list[tuple[str, str, str]]) -> str:
    # rows: (hu_id, epic_id, casos_de_prueba)
    header = "| HU | Epica | Estado | Casos de prueba | Componentes de arquitectura |\n|---|---|---|---|---|\n"
    body = "\n".join(f"| {hu} | {epic} | draft | {tests} | _n/a_ |" for hu, epic, tests in rows)
    return header + body

def _hu_with_gwt(n_scenarios: int) -> str:
    return "\n".join(f"Given a{i} When b{i} Then c{i}" for i in range(n_scenarios))

@pytest.fixture
def base(tmp_path: Path) -> Path:
    req = tmp_path / "docs" / "requirements"
    _write(req / "stories" / "HU-1.1.md", "---\nid: HU-1.1\n---\n" + _hu_with_gwt(1))
    _write(req / "traceability.md", _traceability([("HU-1.1", "EPIC-1", "TEST-1")]))
    tests_dir = tmp_path / "tests"
    _write(tests_dir / "integration" / "test_1.py", "def TEST-1(): pass")
    return tmp_path

def test_validate_qa_clean(base):
    assert validate_qa(base) == []

def test_hu_without_casos_de_prueba_is_reported(base):
    _write(base / "docs" / "requirements" / "traceability.md",
           _traceability([("HU-1.1", "EPIC-1", "_pendiente (fase QA)_")]))
    errors = validate_qa(base)
    assert any("HU-1.1" in e and "Casos de prueba" in e for e in errors)

def test_gwt_scenarios_without_enough_tests_referenced(base):
    _write(base / "docs" / "requirements" / "stories" / "HU-1.1.md",
           "---\nid: HU-1.1\n---\n" + _hu_with_gwt(2))
    # solo un TEST-1 referenciado en traceability, pero la HU tiene 2 escenarios GWT
    errors = validate_qa(base)
    assert any("HU-1.1" in e and "criterio" in e.lower() for e in errors)

def _hu_with_multiline_gwt(n_scenarios: int) -> str:
    # Realistic HU rendering: Given/When/Then each as separate bullet lines,
    # one scenario block per criterio de aceptación.
    blocks = []
    for i in range(n_scenarios):
        blocks.append(
            f"### Criterio {i}\n"
            f"- **Given** a{i}\n"
            f"- **When** b{i}\n"
            f"- **Then** c{i}\n"
        )
    return "\n".join(blocks)

def test_multiline_gwt_scenarios_without_enough_tests_referenced(base):
    _write(base / "docs" / "requirements" / "stories" / "HU-1.1.md",
           "---\nid: HU-1.1\n---\n" + _hu_with_multiline_gwt(2))
    # traceability.md (from `base` fixture) still references only TEST-1,
    # but the HU now has 2 multi-line Given/When/Then scenarios.
    errors = validate_qa(base)
    assert any("HU-1.1" in e and "criterio" in e.lower() for e in errors)

def test_multiline_gwt_scenarios_with_enough_tests_is_clean(base):
    _write(base / "docs" / "requirements" / "stories" / "HU-1.1.md",
           "---\nid: HU-1.1\n---\n" + _hu_with_multiline_gwt(1))
    _write(base / "docs" / "requirements" / "traceability.md",
           _traceability([("HU-1.1", "EPIC-1", "TEST-1")]))
    assert validate_qa(base) == []

def test_hu_with_blank_casos_de_prueba_cell_is_reported(base):
    _write(base / "docs" / "requirements" / "traceability.md",
           "| HU | Epica | Estado | Casos de prueba | Componentes de arquitectura |\n"
           "|---|---|---|---|---|\n"
           "| HU-1.1 | EPIC-1 | draft | | _n/a_ |\n")
    errors = validate_qa(base)
    assert any("HU-1.1" in e and "Casos de prueba" in e for e in errors)

def test_nfr_without_audit_evidence_is_reported(tmp_path: Path):
    arch = tmp_path / "docs" / "architecture"
    _write(arch / "constraints.md", "| NFR-1 | Medida | p95 < 200ms |\n")
    errors = validate_qa(tmp_path)
    assert any("NFR-1" in e and "audit_evidence" in e.lower() for e in errors)

def test_nfr_with_evidence_not_cumple_is_bloqueante(tmp_path: Path):
    arch = tmp_path / "docs" / "architecture"
    _write(arch / "constraints.md", "| NFR-1 | Medida | p95 < 200ms |\n")
    log_path = tmp_path / ".factory" / "log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": "2026-09-02T00:00:00Z", "event_type": "audit_evidence",
        "data": {"nfr": "NFR-1", "medido": "350ms", "objetivo": "p95 < 200ms",
                  "cumple": False, "git_head": "abc123"},
    }
    log_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    errors = validate_qa(tmp_path)
    assert any("NFR-1" in e and "no cumple" in e.lower() for e in errors)

def test_nfr_with_evidence_cumple_is_clean(tmp_path: Path):
    arch = tmp_path / "docs" / "architecture"
    _write(arch / "constraints.md", "| NFR-1 | Medida | p95 < 200ms |\n")
    log_path = tmp_path / ".factory" / "log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": "2026-09-02T00:00:00Z", "event_type": "audit_evidence",
        "data": {"nfr": "NFR-1", "medido": "150ms", "objetivo": "p95 < 200ms",
                  "cumple": True, "git_head": "abc123"},
    }
    log_path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    errors = validate_qa(tmp_path)
    assert errors == []
