from factorysoftware.content import PhaseContent, StepDecl
from factorysoftware.render import build_skill_map


def _content(unidad_principal=None, flujo_skill_name="flujo"):
    return PhaseContent(
        id="requirements",
        unidad_principal=unidad_principal,
        flujo_skill_name=flujo_skill_name,
        steps=[
            StepDecl(id="prd", depende_de=[]),
            StepDecl(id="epics", depende_de=["prd"]),
            StepDecl(id="audit_loop", depende_de=["epics"], rol="Auditor"),
        ],
        preamble="Preámbulo.",
        sections={
            "prd": "Hacé el PRD.",
            "epics": "Hacé las épicas.",
            "audit_loop": "Auditá.",
        },
    )


def test_manual_skills_one_per_step():
    skills = build_skill_map(_content())
    assert "requirements-prd" in skills
    assert "requirements-epics" in skills
    assert "requirements-audit_loop" in skills
    assert "Hacé el PRD." in skills["requirements-prd"]
    assert "Preámbulo." in skills["requirements-prd"]


def test_flujo_skill_contains_all_sections_in_order():
    skills = build_skill_map(_content())
    flujo = skills["requirements-flujo"]
    assert flujo.index("Hacé el PRD.") < flujo.index("Hacé las épicas.") < flujo.index("Auditá.")


def test_flujo_skill_uses_custom_name():
    skills = build_skill_map(_content(flujo_skill_name="e2e"))
    assert "requirements-e2e" in skills
    assert "requirements-flujo" not in skills


def test_no_slide_or_auditor_without_unidad_principal():
    skills = build_skill_map(_content())
    assert not any(k.endswith("-slide") for k in skills)
    assert "requirements-auditor" not in skills


def test_slide_and_auditor_present_with_unidad_principal():
    skills = build_skill_map(_content(unidad_principal="slide"))
    assert "requirements-slide" in skills
    assert "requirements-auditor" in skills


def test_auditor_skill_only_has_auditor_role_sections():
    skills = build_skill_map(_content(unidad_principal="slide"))
    auditor = skills["requirements-auditor"]
    assert "Auditá." in auditor
    assert "Hacé el PRD." not in auditor
