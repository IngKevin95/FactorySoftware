from pathlib import Path
import yaml
from factorysoftware.cli import main


def _fm(data: dict, body: str = "") -> str:
    return f"---\n{yaml.dump(data, allow_unicode=True)}---\n{body}"


def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_validate_construction(tmp_path: Path):
    assert main(["validate", "construction", "--project-root", str(tmp_path)]) == 0


def test_cli_validate_construction_fails_on_role_without_content_pack(tmp_path: Path):
    arch = tmp_path / "docs" / "architecture"
    cons = tmp_path / "docs" / "construction" / "plan"
    _write(arch / "apis" / "API-1.md", _fm({"id": "API-1"}))
    _write(cons / "EPIC-1-plan.md", _fm(
        {"id": "EPIC-1", "estado": "draft", "depende_de_epicas": []},
        "### TASK-1.1\n- rol: frontend\n- implementa: API-1\n- depende_de: []",
    ))
    assert main(["validate", "construction", "--project-root", str(tmp_path)]) == 0


def test_audit_triage(tmp_path: Path):
    assert main(["audit-triage", "--epic", "EPIC-1", "--project-root", str(tmp_path)]) == 0


def test_audit_triage_reads_epic_n_plan_md_and_triggers_fidelity_for_frontend_role(
    tmp_path: Path, capsys
):
    cons = tmp_path / "docs" / "construction" / "plan"
    _write(cons / "EPIC-1-plan.md", _fm(
        {"id": "EPIC-1", "estado": "draft", "depende_de_epicas": []},
        "### TASK-1.1\n- rol: frontend\n- implementa: API-1\n- depende_de: []",
    ))
    assert main(["audit-triage", "--epic", "EPIC-1", "--project-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "fidelity" in out
    assert "usability" in out


def test_audit_triage_reads_epic_n_plan_md_and_triggers_security_for_seguridad_role(
    tmp_path: Path, capsys
):
    cons = tmp_path / "docs" / "construction" / "plan"
    _write(cons / "EPIC-1-plan.md", _fm(
        {"id": "EPIC-1", "estado": "draft", "depende_de_epicas": []},
        "### TASK-1.1\n- rol: seguridad\n- implementa: API-1\n- depende_de: []",
    ))
    assert main(["audit-triage", "--epic", "EPIC-1", "--project-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "security" in out
