# Catálogo de Skills, Sub-agentes y Auditores por Fábrica

Estado: referencia (derivado de los 5 specs ya aprobados, no es un spec
nuevo — se regenera a mano si los pipelines cambian)
Fuente: `2026-08-19-factory-core-design.md` +
`2026-08-19-{requirements,architecture,construction,qa}-skill-design.md`

Convención de nombres de skill (definida en el núcleo): cada fase se expone
como un skill orquestador `<fase>` (modo automático, encadena todos los
pasos) más un skill por paso declarado `<fase>-<paso>` (modo manual, con
chequeo de prerequisitos). En proveedores de archivo único (Copilot/Codex/
OpenCode/Antigravity si no confirma multi-archivo) ambos modos viven como
secciones del mismo archivo de instrucciones.

## Personas transversales (núcleo, no son pasos de ninguna fase)

| Persona | Archivo fuente | Rol |
|---|---|---|
| Asesor | `content/advisor.md` | Pros/contras honestos *durante* la construcción de un artefacto, puede diferir del pedido del usuario |
| Auditor | `content/auditor.md` | Corre el checklist de **una sola fase**, contra su propio criterio de completitud/coherencia interna |
| Auditor Integral | `content/auditor_integral.md` | Corre **después** del Auditor de fase, valida coherencia entre la fase que cierra y la fase anterior que le dio origen. No aplica en Requerimientos (primera fase, no hay fase anterior) |

Ambos auditores se despachan como sub-agente independiente si el proveedor
lo soporta, o como autocrítica estructurada si no. Hallazgos con severidad
Bloqueante/Mayor/Menor; solo Bloqueante frena el gate.

---

## 1. Requerimientos (`requirements`)

Sin fase anterior — no tiene Auditor Integral.

| Paso (skill manual) | Tipo | Fan-out | Rol/Auditor |
|---|---|---|---|
| `requirements-prd` | agéntico | — | constructor |
| `requirements-epics` | agéntico | — | constructor + Asesor (sugerencia transversal obligatoria) |
| `requirements-hu_por_epica` | agéntico | 1 por Épica, paralelo | constructor |
| `requirements-traceability` | mecánico/agéntico | — | constructor (agrega resultado) |
| `requirements-flujos` | agéntico | — | constructor (ve todas las HU juntas) |
| `requirements-audit_loop` | agéntico | — | **Auditor** (checklist 1–11, sin Auditor Integral) |

Gate: aprobación humana explícita de PRD + Épicas + HU + Flujos.

---

## 2. Arquitectura (`architecture`)

| Paso (skill manual) | Tipo | Fan-out | Rol/Auditor |
|---|---|---|---|
| `architecture-constraints` | agéntico | — | constructor (restricciones + NFR medibles) |
| `architecture-adrs` | agéntico | — | constructor + Asesor (fundamento teórico obligatorio) |
| `architecture-adrs_audit` | agéntico | — | **Auditor** (checkpoint temprano, checklist a–e, antes de que nada más construya sobre una ADR mala) |
| `architecture-overview` | agéntico | — | constructor |
| `architecture-data_model` | agéntico | — | constructor |
| `architecture-apis` | agéntico | 1 por HU con anexo de endpoint, paralelo | constructor |
| `architecture-screens` | agéntico | 1 por HU con anexo de pantalla, paralelo | constructor (debe honrar `FLUJO-N` de Requerimientos) |
| `architecture-ui_prototype` | agéntico | 1 por `SCREEN-N`, paralelo | constructor (código real corrible, no descartable) |
| `architecture-gap_check_and_traceability` | agéntico | — | **Auditor** (checklist estructural 1–6 + semántico 7–11) |
| `architecture-integral_audit` | agéntico | — | **Auditor Integral** (contra Requerimientos completo) |

Gate: aprobación humana de ADRs + overview + data model + APIs + pantallas
+ prototipo corrible.

---

## 3. Construcción (`construction`)

| Paso (skill manual) | Tipo | Fan-out | Rol/Auditor |
|---|---|---|---|
| `construction-task_planning` | agéntico | 1 por Épica, paralelo | constructor (catálogo de roles: backend/data/frontend base, seguridad/automatizaciones/mobile condicionales) |
| `construction-plan_audit` | agéntico | — | **Auditor** (ve todos los planes juntos, escribe `depende_de_epicas`) |
| `construction-plan_integral_audit` | agéntico | — | **Auditor Integral** (planes vs Arquitectura completa) |
| `construction-branch_setup` | mecánico | 1 por Épica, paralelo (serie si depende de otra Épica) | — (git, no agente) |
| `construction-task_execution` | agéntico | 1 por `TASK-N.M`, paralelo | sub-agentes de rol: `backend`, `data`, `frontend`, `seguridad`, `automatizaciones`, `mobile` — cada uno hace TDD inline (rojo→verde→refactor) |
| `construction-worktree_integration` | mecánico | 1 por Épica, paralelo | — (git merge) |
| `construction-audit_triage` | mecánico | 1 por Épica, paralelo | — (decide por diff real qué dimensiones auditar) |
| `construction-construction_audit` | agéntico | 1 por dimensión activada: `audit_functionality`, `audit_practices`, `audit_security`, `audit_efficiency` | **Auditor** (4 sub-auditores independientes, ver detalle abajo) |
| `construction-construction_integral_audit` | agéntico | 1 por Épica, paralelo | **Auditor Integral** (código vs Arquitectura + Requerimientos + `develop` real ya integrado — cubre lo que sería un "outer loop" sin paso aparte) |
| `construction-pr_gate` | mecánico + pregunta | 1 por Épica, paralelo | — (abre PR real a `develop`) |

### Detalle de `construction_audit` (4 sub-auditores)

| Sub-auditor | Qué mira | Se dispara siempre? |
|---|---|---|
| `audit_functionality` | Tests reales pasan (gate de TDD mecánico), contrato API/SCREEN respetado, AC cumplido en comportamiento real | Sí, siempre |
| `audit_practices` | Escalera Beck → SOLID/GRASP → patrones GoF (del `CLAUDE.md` del proyecto), detección de sobreingeniería | Sí, siempre |
| `audit_security` | Validación de inputs, authn/authz, secretos | Solo si `audit_triage` lo activa (diff toca auth o hay `TASK` de rol seguridad) |
| `audit_efficiency` | Uso idiomático del stack, costo/complejidad por función | Solo si `audit_triage` lo activa (loops anidados, queries nuevas) |

Gate: PR a `develop` (merge commit `--no-ff`) por Épica.

---

## 4. QA (`qa`)

| Paso (skill manual) | Tipo | Fan-out | Rol/Auditor |
|---|---|---|---|
| `qa-coverage_gap_analysis` | agéntico | — | constructor (arma `docs/qa/plan.md`) |
| `qa-qa_branch_setup` | mecánico | — | — (una sola rama para toda la fase) |
| `qa-integration_tests` | agéntico | 1 por `TEST-N` tipo integration, paralelo | constructor |
| `qa-e2e_tests` | agéntico | 1 por `TEST-N` tipo e2e (uno por `FLUJO-N`), paralelo | constructor |
| `qa-nfr_tests` | agéntico | 1 por `TEST-N` tipo nfr (uno por `NFR-N`), paralelo | constructor (mide de verdad, no code review) |
| `qa-security_tests` | agéntico | — | constructor (pasada única, holística, SAST + escenarios) |
| `qa-traceability_update` | mecánico | — | — (completa columna "Casos de prueba") |
| `qa-qa_audit` | mecánico + agéntico | `audit_coverage` [mecánico], `audit_nfr_compliance` [mecánico], `audit_test_quality` [agéntico], `audit_security_findings` [agéntico] | **Auditor** |
| `qa-qa_integral_audit` | agéntico | — | **Auditor Integral** (contra Construcción/Arquitectura/Requerimientos completos) |
| `qa-pr_gate` | mecánico + pregunta | — | — (abre PR único de QA a `develop`) |

Gate: PR único de `feature/qa-coverage-...` a `develop`.

---

## Resumen: cuántos sub-agentes reales por fase (proyecto de ejemplo, 3 Épicas — ver conversación previa para el detalle número a número)

| Fase | Pasos agénticos | Pasos mecánicos | Auditor de fase | Auditor Integral |
|---|---|---|---|---|
| Requerimientos | 5 (uno con fan-out) | 0 | 1 (sin Integral) | — |
| Arquitectura | 8 (tres con fan-out) | 0 | 1 | 1 |
| Construcción | 5 (tres con fan-out) | 5 (todos con fan-out por Épica) | 2 (plan + 4 dimensiones) | 2 |
| QA | 6 (tres con fan-out) | 3 | 2 (2 mecánicas + 2 agénticas) | 1 |

El costo real en invocaciones crece con la cantidad de Épicas/HU/flujos —
ya lo cuantificamos con un ejemplo concreto (~60 invocaciones para 3
Épicas, Requerimientos+Arquitectura+Construcción, sin contar QA ni
reintentos de loop) en la conversación que originó este catálogo.
