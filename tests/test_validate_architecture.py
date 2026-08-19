import pytest
from pathlib import Path
import yaml
from factorysoftware.architecture.validator import validate_architecture

def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"

def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

@pytest.fixture
def docs(tmp_path: Path) -> Path:
    docs_dir = tmp_path / "docs"
    req_dir = docs_dir / "requirements"
    arch_dir = docs_dir / "architecture"
    _write(req_dir / "stories" / "HU-1.1.md", _fm({"id": "HU-1.1", "estado": "draft"}))
    _write(req_dir / "traceability.md", "| HU | Epica | Estado | CP | Componentes de arquitectura |\n|----|-------|--------|----|------------------------------|\n| HU-1.1 | EPIC-1 | draft | _p_ | API-1, SCREEN-1 |")
    _write(arch_dir / "apis" / "API-1.md", _fm({"id": "API-1", "implementa": ["HU-1.1"]}))
    _write(arch_dir / "screens" / "SCREEN-1.md", _fm({"id": "SCREEN-1", "implementa": ["HU-1.1"], "apis_consumidas": ["API-1"]}))
    # dummy prototype to pass check 6
    _write(tmp_path / "prototype" / "SCREEN-1.html", "mock")
    _write(arch_dir / "constraints.md", "| ID | Estímulo |\n|----|----------|\n| NFR-1 | Algo |")
    _write(arch_dir / "adrs" / "ADR-1.md", _fm({"id": "ADR-1", "nfr_aplicados": ["NFR-1"]}))
    return tmp_path

def test_validate_architecture_clean(docs):
    assert validate_architecture(docs) == []

def test_missing_api_for_hu(docs):
    _write(docs / "docs" / "requirements" / "stories" / "HU-1.2.md", _fm({"id": "HU-1.2", "estado": "draft"}, "Anexo endpoint: x"))
    errors = validate_architecture(docs)
    assert any("HU-1.2" in e and "API" in e for e in errors)

def test_missing_screen_for_hu(docs):
    _write(docs / "docs" / "requirements" / "stories" / "HU-1.3.md", _fm({"id": "HU-1.3", "estado": "draft"}, "Anexo pantalla: x"))
    errors = validate_architecture(docs)
    assert any("HU-1.3" in e and "SCREEN" in e for e in errors)

def test_missing_api_in_screen_apis_consumidas(docs):
    _write(docs / "docs" / "architecture" / "screens" / "SCREEN-2.md", _fm({"id": "SCREEN-2", "apis_consumidas": ["API-99"]}))
    errors = validate_architecture(docs)
    assert any("API-99" in e for e in errors)

def test_implementa_inexistent_hu(docs):
    _write(docs / "docs" / "architecture" / "apis" / "API-2.md", _fm({"id": "API-2", "implementa": ["HU-9.9"]}))
    errors = validate_architecture(docs)
    assert any("HU-9.9" in e for e in errors)

def test_missing_prototype_for_screen(docs):
    _write(docs / "docs" / "architecture" / "screens" / "SCREEN-3.md", _fm({"id": "SCREEN-3", "implementa": []}))
    errors = validate_architecture(docs)
    assert any("SCREEN-3" in e and "prototipo" in e.lower() for e in errors)

def test_unattended_nfr(docs):
    _write(docs / "docs" / "architecture" / "constraints.md", "| ID |\n|----|\n| NFR-99 |")
    errors = validate_architecture(docs)
    assert any("NFR-99" in e for e in errors)
