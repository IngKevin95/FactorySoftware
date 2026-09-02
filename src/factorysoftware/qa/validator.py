from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
        return yaml.safe_load(text[3:end]) or {}
    except (ValueError, yaml.YAMLError):
        return {}


_GIVEN_RE = re.compile(r"\bGiven\b")
_TRACE_ROW_RE = re.compile(r"^\|\s*(HU-\d+\.\d+)\s*\|[^|]*\|[^|]*\|([^|]*)\|")
_NFR_ROW_RE = re.compile(r"\|\s*(NFR-\d+)\s*\|")


def validate_qa(project_root: Path) -> list[str]:
    """
    Validaciones estructurales de la fase de QA.

    Check 1: cada HU en traceability.md tiene una celda no vacía en "Casos de prueba".
    Check 2: cada HU tiene al menos tantos tests referenciados en traceability.md
             como escenarios Given/When/Then en su archivo de historia.
    Check 3: cada NFR en constraints.md tiene un evento audit_evidence con git_head
             en .factory/log.jsonl.
    Check 4: cada NFR con evidencia debe tener cumple=True, si no es hallazgo bloqueante.
    """
    errors: list[str] = []
    docs = project_root / "docs"

    trace_path = docs / "requirements" / "traceability.md"
    trace_tests: dict[str, list[str]] = {}
    if trace_path.exists():
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            m = _TRACE_ROW_RE.match(line.strip())
            if not m:
                continue
            hu_id, cell = m.group(1), m.group(2).strip()
            if not cell or (cell.startswith("_") and cell.endswith("_")):
                trace_tests[hu_id] = []
                errors.append(
                    f"Check 1: HU '{hu_id}' has no 'Casos de prueba' referenced in traceability.md"
                )
            else:
                trace_tests[hu_id] = [t.strip() for t in cell.split(",") if t.strip()]

    stories_dir = docs / "requirements" / "stories"
    if stories_dir.exists():
        for hu_path in stories_dir.glob("HU-*.md"):
            text = hu_path.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            hu_id = fm.get("id", hu_path.stem)
            n_scenarios = len(_GIVEN_RE.findall(text))
            n_tests = len(trace_tests.get(hu_id, []))
            if n_scenarios > 0 and n_tests < n_scenarios:
                errors.append(
                    f"Check 2: HU '{hu_id}' has {n_scenarios} Given/When/Then criterio(s) "
                    f"but only {n_tests} test(s) referenced in traceability.md"
                )

    constraints_path = docs / "architecture" / "constraints.md"
    nfr_ids: set[str] = set()
    if constraints_path.exists():
        nfr_ids = set(_NFR_ROW_RE.findall(constraints_path.read_text(encoding="utf-8")))

    log_path = project_root / ".factory" / "log.jsonl"
    evidence_by_nfr: dict[str, dict] = {}
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("event_type") != "audit_evidence":
                continue
            data = entry.get("data", {})
            nfr = data.get("nfr")
            if nfr:
                evidence_by_nfr[nfr] = data

    for nfr in sorted(nfr_ids):
        evidence = evidence_by_nfr.get(nfr)
        if evidence is None or not evidence.get("git_head"):
            errors.append(
                f"Check 3: NFR '{nfr}' has no audit_evidence event with git_head in log.jsonl"
            )
            continue
        if not evidence.get("cumple", False):
            errors.append(
                f"Check 4: NFR '{nfr}' no cumple su objetivo "
                f"(medido={evidence.get('medido')!r}, objetivo={evidence.get('objetivo')!r})"
            )

    return errors
