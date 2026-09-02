import pytest
from pathlib import Path
import yaml
from factorysoftware.construction.validator import validate_construction

def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"

def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

@pytest.fixture
def docs(tmp_path: Path) -> Path:
    req = tmp_path / "docs" / "requirements"
    arch = tmp_path / "docs" / "architecture"
    cons = tmp_path / "docs" / "construction" / "plan"
    _write(req / "traceability.md", "| HU | Implementado |\n|---|---|\n| HU-1.1 | _p_ |")
    _write(arch / "apis" / "API-1.md", _fm({"id": "API-1"}))
    _write(arch / "adrs" / "ADR-1.md", _fm({"id": "ADR-1"}))
    _write(cons / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: backend\n- implementa: API-1\n- depende_de: []"))
    return tmp_path

def test_validate_construction_clean(docs):
    assert validate_construction(docs) == []

def test_missing_api_reference(docs):
    _write(docs / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: backend\n- implementa: API-99\n- depende_de: []"))
    errors = validate_construction(docs)
    assert any("API-99" in e for e in errors)

def test_circular_dependency(docs):
    _write(docs / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- depende_de: [TASK-1.2]\n\n### TASK-1.2\n- depende_de: [TASK-1.1]"))
    errors = validate_construction(docs)
    assert any("circular" in e.lower() for e in errors)

def test_invalid_role(docs):
    _write(docs / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: alien\n- implementa: API-1\n- depende_de: []"))
    errors = validate_construction(docs)
    assert any("alien" in e for e in errors)

def test_role_without_content_pack_is_reported(tmp_path):
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "backend.md").write_text("rol backend", encoding="utf-8")
    # "frontend" se usa en el plan pero no tiene content pack en roles_dir
    _write(tmp_path / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: frontend\n- implementa: API-1\n- depende_de: []"))
    _write(tmp_path / "docs" / "architecture" / "apis" / "API-1.md", _fm({"id": "API-1"}))
    errors = validate_construction(tmp_path, content_roles_dir=roles_dir)
    assert any("frontend" in e and "content pack" in e.lower() for e in errors)

def test_role_with_content_pack_is_clean(tmp_path):
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "backend.md").write_text("rol backend", encoding="utf-8")
    _write(tmp_path / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: backend\n- implementa: API-1\n- depende_de: []"))
    _write(tmp_path / "docs" / "architecture" / "apis" / "API-1.md", _fm({"id": "API-1"}))
    errors = validate_construction(tmp_path, content_roles_dir=roles_dir)
    assert errors == []

def test_role_check_skipped_when_no_roles_dir_given(tmp_path):
    # comportamiento actual sin cambios: sin content_roles_dir, no valida existencia de pack
    _write(tmp_path / "docs" / "construction" / "plan" / "EPIC-1-plan.md", _fm({
        "id": "EPIC-1", "estado": "draft", "depende_de_epicas": []
    }, "### TASK-1.1\n- rol: backend\n- implementa: API-1\n- depende_de: []"))
    _write(tmp_path / "docs" / "architecture" / "apis" / "API-1.md", _fm({"id": "API-1"}))
    errors = validate_construction(tmp_path)
    assert errors == []
