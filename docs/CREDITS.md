# Créditos y Atribuciones

FactorySoftware no depende de estos repositorios (no son dependencias en
`pyproject.toml`, no se invocan en runtime). Cuando un patrón, convención o
estructura de skill se adapta de ellos, el trabajo se reescribe en Markdown/Python
propio del proyecto y se referencia acá.

Base metodológica del proyecto: **Superpowers** (`docs/superpowers/specs` y
`docs/superpowers/plans`, flujo spec → plan → execute). Todo lo demás se evalúa
como complemento, nunca como reemplazo.

## Fuentes de patrones adaptados

| Repo | Autor | Licencia (del skill fuente) | Qué se adaptó (y dónde) |
|---|---|---|---|
| [gentle-ai](https://github.com/Gentleman-Programming/gentle-ai) | Gentleman Programming | Apache-2.0 (`skills/branch-pr`, `skills/work-unit-commits`) | Convención de nombres de rama (`branch_setup`), commits por unidad de trabajo y presupuesto de 400 líneas por PR (`task_execution`) → `content/construction.md` |
| [gentle-pi](https://github.com/Gentleman-Programming/gentle-pi) | Gentleman Programming | Apache-2.0 (`skills/rdd-defect-workflow`) | Regla "una causa, un PR" (no agrupar fixes independientes) → `content/construction.md`, paso `pr_gate` |
| [engram](https://github.com/Gentleman-Programming/engram) | Gentleman Programming | Apache-2.0 (`skills/memory-protocol`) | Convención de qué/cuándo registrar memoria (decisión, bugfix, resumen de sesión) reusando el `factory log` existente (`event_type=memory`), sin adoptar el binario Go ni SQLite → `content/construction.md`, pasos `task_execution` y `pr_gate` |
| [agent-teams-lite](https://github.com/Gentleman-Programming/agent-teams-lite) | Gentleman Programming | MIT | Patrón orquestador + subagentes en Markdown puro |
| [gentleman-architecture-agents](https://github.com/Gentleman-Programming/gentleman-architecture-agents) | Gentleman Programming | MIT | Scope Rule para validación de arquitectura — candidato para `content/architecture.md` |
| [gentleman-guardian-angel](https://github.com/Gentleman-Programming/gentleman-guardian-angel) | Gentleman Programming | MIT | Checklist de code review agnóstico de proveedor — candidato para `content/qa.md` |
| [Gentleman-Skills](https://github.com/Gentleman-Programming/Gentleman-Skills) | Gentleman Programming | — (ver repo) | Catálogo de referencia de skills community |

## Fuentes propias (otros proyectos del mismo usuario)

Estos no son repos de terceros — son proyectos propios del autor de este repo,
citados igual por trazabilidad de dónde salió el patrón.

| Repo | Qué se adaptó (y dónde) |
|---|---|
| `DemoWhatsappAgent/.claude/hooks/build/gitflow-guard.sh` | Enforcement de convención de nombres de rama (`feat\|fix\|chore\|docs\|style\|refactor\|perf\|test\|build\|ci\|revert/<slug>`) agregado al `GUARD_SCRIPT` compartido en `adapters/base.py` (antes solo bloqueaba commit/push directo a main/develop, ahora también valida el nombre de la rama en `git commit`) |
| `DemoWhatsappAgent/.claude/state/build-state.json` + `build-state.schema.json` | Estado vivo por-épica: `SliceState` (`state.py`) → `.factory/slices/<epic>.json`, expuesto por `factory slice show\|gate\|progress\|wiring add\|wiring status`. Versión reducida: sin `active_slice`/`history`/`releases` agregados (no existe ese concepto acá todavía), sin JSON Schema aparte (el modelo Pydantic ya valida) |
| `DemoWhatsappAgent/.claude/agents/build/wiring-adversarial-verifier.md` | Paso `wiring_check` en `content/construction.md`, entre `construction_integral_audit` y `pr_gate` — verificación adversarial de cableado antes de abrir PR |
| `DemoWhatsappAgent/.claude/memory/*.md` + `MEMORY.md` | Paso `project_memory_setup` (paralelo a `epics`) en `content/requirements.md` → `docs/memory/*.md`, idempotente. Categorías generalizadas del ejemplo (design_source, deterministic_layer, external_service_layer, high_stakes_decisions, sensitive_data, server_side_secrets) |
| `FabricaAgenticaClaude/.claude/IMPROVEMENTS-AND-OVERENGINEERING.md` | Negativo: confirma no portar capas de indirección que solo delegan ni duplicar carpetas de workflow por versionado |

## Roles como subagentes nativos

Implementado (a pedido explícito, tras una primera evaluación que lo había diferido): `content/roles/{frontend,backend,data,seguridad,automatizaciones,mobile}.md` — cada uno un content pack standalone (`name: role-<rol>`) con alcance, límites y reglas duras propias del rol.

- **Origen del patrón:** `YarnovaSoft/.opencode/agents/*.md` (persona por rol vía frontmatter nativo) + `DemoWhatsappAgent/.claude/agents/build/*.md` (agentes especializados por gate, con `tools` acotadas).
- **Mecanismo:** `adapters/base.py` agrega `is_role_skill`/`role_name`/`role_description` (branch por prefijo `role-`, sin nueva interfaz ni runtime). `adapters/claude_code.py` instala en `.claude/agents/<rol>.md` (frontmatter `name`/`description`/`tools`); `adapters/opencode.py` instala en `.opencode/agents/<rol>.md` (frontmatter `description`/`mode: subagent`) — igual a los ejemplos fuente. `installer.py` pasó a leer `content/**/*.md` (antes solo el nivel superior) para levantar la subcarpeta `roles/`.
- **Antigravity/Codex/Copilot:** sin schema de subagente nativo verificado (Antigravity) o sin ese concepto (Codex/Copilot de archivo único) — los packs de rol se instalan igual pero degradan a skill/sección normal, no a agente separado.
- **`content/construction.md`, paso `task_planning`:** documenta el despacho — si el host soporta subagentes nativos, cada tarea se delega al agente `role-<rol>`; si no, el agente genérico aplica las reglas del rol manualmente.

Cada fila queda "pendiente" hasta que el contenido efectivamente se copie/adapte
a un archivo de este repo; en ese momento el commit que lo introduce debe
referenciar esta tabla en su mensaje.

## Nota legal

Los repos de Gentleman Programming citados con licencia MIT permiten copiar y
adaptar código/contenido siempre que se preserve el aviso de copyright
original. Al portar un fragmento textual (no solo el patrón/idea), agregar el
aviso correspondiente como comentario en el archivo destino, ej.:

```
# Adaptado de gentle-ai (MIT) - Copyright (c) 2025 Gentleman Programming
# https://github.com/Gentleman-Programming/gentle-ai
```
