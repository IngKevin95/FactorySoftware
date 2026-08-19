from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel

_SECTION_RE = re.compile(r"^## Paso: (?P<id>\S+)\s*$", re.MULTILINE)


class StepDecl(BaseModel):
    id: str
    depende_de: list[str] = []
    fan_out: str | None = None
    paralelizable: bool = False
    rol: str | None = None


class PhaseContent(BaseModel):
    id: str
    unidad_principal: str | None = None
    flujo_skill_name: str = "flujo"
    steps: list[StepDecl]
    preamble: str
    sections: dict[str, str]


def parse_content(path: Path) -> PhaseContent:
    text = path.read_text(encoding="utf-8")
    _, frontmatter_raw, body = text.split("---", 2)
    frontmatter = yaml.safe_load(frontmatter_raw)
    steps = [StepDecl(**s) for s in frontmatter["steps"]]

    matches = list(_SECTION_RE.finditer(body))
    preamble = body[: matches[0].start()].strip() if matches else body.strip()
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[m.group("id")] = body[start:end].strip()

    return PhaseContent(
        id=frontmatter["id"],
        unidad_principal=frontmatter.get("unidad_principal"),
        flujo_skill_name=frontmatter.get("flujo_skill_name", "flujo"),
        steps=steps,
        preamble=preamble,
        sections=sections,
    )
