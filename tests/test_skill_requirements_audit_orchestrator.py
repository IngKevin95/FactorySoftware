from __future__ import annotations
import json
from pathlib import Path
import pytest


EXPECTED_STEPS = ["prd", "epics", "hu_por_epica", "traceability", "flujos", "audit_loop"]


@pytest.fixture
def full_run_log(tmp_path: Path) -> Path:
    log = tmp_path / ".factory" / "log.jsonl"
    log.parent.mkdir(parents=True)
    events = [
        {"type": "advisor_note", "category": "sugerencia_transversal",
         "step": "epics", "suggestions": [], "accepted": []},
        {"type": "step_complete", "step": "prd",
         "output_files": ["docs/requirements/PRD.md"]},
        {"type": "step_complete", "step": "epics",
         "output_files": ["docs/requirements/epics/EPIC-1.md"]},
        {"type": "step_complete", "step": "hu_por_epica", "epic": "EPIC-1",
         "output_files": ["docs/requirements/stories/HU-1.1.md"]},
        {"type": "step_complete", "step": "traceability",
         "output_files": ["docs/requirements/traceability.md"]},
        {"type": "step_complete", "step": "flujos",
         "output_files": ["docs/requirements/flujos/FLUJO-1.md"]},
        {"type": "step_complete", "step": "audit_loop",
         "iterations": 1, "approved_by": "user"},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return tmp_path


def test_all_pipeline_steps_logged(full_run_log):
    events = [json.loads(l) for l in
              (full_run_log / ".factory" / "log.jsonl").read_text().splitlines()]
    completed = {e["step"] for e in events if e.get("type") == "step_complete"}
    for step in EXPECTED_STEPS:
        assert step in completed, f"Missing step_complete for: {step}"


def test_audit_loop_approved_by_user(full_run_log):
    events = [json.loads(l) for l in
              (full_run_log / ".factory" / "log.jsonl").read_text().splitlines()]
    audit = [e for e in events
             if e.get("step") == "audit_loop" and e.get("type") == "step_complete"]
    assert len(audit) == 1
    assert audit[0]["approved_by"] == "user"
    assert 1 <= audit[0]["iterations"] <= 3


def test_advisor_note_before_epics_close(full_run_log):
    events = [json.loads(l) for l in
              (full_run_log / ".factory" / "log.jsonl").read_text().splitlines()]
    notes = [e for e in events
             if e.get("type") == "advisor_note"
             and e.get("category") == "sugerencia_transversal"]
    assert len(notes) >= 1
