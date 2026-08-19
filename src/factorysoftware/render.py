from __future__ import annotations

from factorysoftware.content import PhaseContent

_AUDITOR_ROLES = {"Auditor", "Auditor Integral"}


def _joined_sections(content: PhaseContent) -> str:
    return "\n\n".join(content.sections[s.id] for s in content.steps)


def build_skill_map(content: PhaseContent) -> dict[str, str]:
    skills: dict[str, str] = {}

    for step in content.steps:
        skill_id = f"{content.id}-{step.id}"
        skills[skill_id] = f"{content.preamble}\n\n{content.sections[step.id]}\n"

    flujo_id = f"{content.id}-{content.flujo_skill_name}"
    skills[flujo_id] = (
        f"{content.preamble}\n\n{_joined_sections(content)}\n\n"
        "(Ejecutar todos los pasos anteriores en orden, encadenados, sin "
        "parar a esperar confirmación entre pasos intermedios.)\n"
    )

    if content.unidad_principal:
        slide_id = f"{content.id}-{content.unidad_principal}"
        skills[slide_id] = (
            f"{content.preamble}\n\n{_joined_sections(content)}\n\n"
            "(Ejecutar acotado a la unidad recibida como argumento de invocación.)\n"
        )

        auditor_sections = "\n\n".join(
            content.sections[s.id] for s in content.steps if s.rol in _AUDITOR_ROLES
        )
        skills[f"{content.id}-auditor"] = f"{content.preamble}\n\n{auditor_sections}\n"

    return skills
