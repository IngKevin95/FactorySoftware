from __future__ import annotations
import json
from pathlib import Path
import yaml
import pytest


def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"


# --- HU contract ---

@pytest.fixture
def hu_output(tmp_path: Path) -> Path:
    hu = tmp_path / "docs" / "requirements" / "stories" / "HU-1.1.md"
    hu.parent.mkdir(parents=True)
    hu.write_text(
        _fm({"id": "HU-1.1", "epica": "EPIC-1", "estado": "draft",
             "prioridad": "alta", "depende_de": []},
            "Como usuario quiero algo para algo.\n\n"
            "**Given** usuario existe **When** hace login **Then** ve dashboard\n"),
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "step_complete", "step": "hu_por_epica",
                    "epic": "EPIC-1",
                    "output_files": ["docs/requirements/stories/HU-1.1.md"]}) + "\n"
    )
    return tmp_path


def test_hu_file_exists(hu_output):
    assert (hu_output / "docs" / "requirements" / "stories" / "HU-1.1.md").exists()


def test_hu_frontmatter_complete(hu_output):
    text = (hu_output / "docs" / "requirements" / "stories" / "HU-1.1.md").read_text()
    fm = yaml.safe_load(text.split("---")[1])
    assert fm["id"] == "HU-1.1"
    assert fm["epica"] == "EPIC-1"
    assert "prioridad" in fm
    assert isinstance(fm.get("depende_de", []), list)


def test_hu_has_gwt(hu_output):
    text = (hu_output / "docs" / "requirements" / "stories" / "HU-1.1.md").read_text()
    assert "Given" in text and "When" in text and "Then" in text


def test_hu_step_complete_logged(hu_output):
    events = [json.loads(l) for l in
              (hu_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events
            if e.get("type") == "step_complete" and e.get("step") == "hu_por_epica"]
    assert len(done) >= 1
    # "epic" is the field that distinguishes fan-out instances in the log -
    # the one field this whole design depends on.
    assert done[0]["epic"] == "EPIC-1"


# --- Traceability contract ---

@pytest.fixture
def trace_output(tmp_path: Path) -> Path:
    t = tmp_path / "docs" / "requirements" / "traceability.md"
    t.parent.mkdir(parents=True)
    t.write_text(
        "| HU | Epica | Estado | Casos de prueba | Componentes de arquitectura |\n"
        "|----|-------|--------|------------------|------------------------------|\n"
        "| HU-1.1 | EPIC-1 | draft | _pendiente (fase QA)_ | _pendiente (fase Arquitectura)_ |\n"
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "step_complete", "step": "traceability",
                    "output_files": ["docs/requirements/traceability.md"]}) + "\n"
    )
    return tmp_path


def test_traceability_file_exists(trace_output):
    assert (trace_output / "docs" / "requirements" / "traceability.md").exists()


def test_traceability_has_hu_row(trace_output):
    assert "HU-1.1" in (trace_output / "docs" / "requirements" / "traceability.md").read_text()


def test_traceability_step_complete_logged(trace_output):
    events = [json.loads(l) for l in
              (trace_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events
            if e.get("step") == "traceability" and e.get("type") == "step_complete"]
    assert len(done) == 1


# --- Flujos contract ---

@pytest.fixture
def flujos_output(tmp_path: Path) -> Path:
    flujo = tmp_path / "docs" / "requirements" / "flujos" / "FLUJO-1.md"
    flujo.parent.mkdir(parents=True)
    flujo.write_text(
        _fm({"id": "FLUJO-1", "estado": "draft", "hu": ["HU-1.1", "HU-2.1"]},
            "## Alta de cuenta y primer login\n\n"
            "Paso 1 (HU-1.1): el usuario completa el formulario.\n"
            "Paso 2 (HU-2.1): el sistema le muestra el dashboard.\n\n"
            "## Criterio de exito del flujo\n"
            "El usuario ve el dashboard despues de completar el alta.\n"),
    )
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir()
    log.write_text(
        json.dumps({"type": "step_complete", "step": "flujos",
                    "output_files": ["docs/requirements/flujos/FLUJO-1.md"]}) + "\n"
    )
    return tmp_path


def test_flujo_file_exists(flujos_output):
    assert (flujos_output / "docs" / "requirements" / "flujos" / "FLUJO-1.md").exists()


def test_flujo_frontmatter_valid(flujos_output):
    text = (flujos_output / "docs" / "requirements" / "flujos" / "FLUJO-1.md").read_text()
    fm = yaml.safe_load(text.split("---")[1])
    assert fm["id"] == "FLUJO-1"
    assert isinstance(fm["hu"], list) and len(fm["hu"]) >= 1


def test_flujo_has_success_criterion(flujos_output):
    text = (flujos_output / "docs" / "requirements" / "flujos" / "FLUJO-1.md").read_text()
    assert "criterio" in text.lower() or "Criterio" in text


def test_flujos_step_complete_logged(flujos_output):
    events = [json.loads(l) for l in
              (flujos_output / ".factory" / "log.jsonl").read_text().splitlines()]
    done = [e for e in events
            if e.get("step") == "flujos" and e.get("type") == "step_complete"]
    assert len(done) == 1
