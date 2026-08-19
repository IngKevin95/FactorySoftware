# Skill de QA Integral — Diseño

Estado: aprobado
Subsistema: 5 de N (fase de contenido: QA) — depende del núcleo,
Requerimientos, Arquitectura y Construcción:
- `docs/superpowers/specs/2026-08-19-factory-core-design.md`
- `docs/superpowers/specs/2026-08-19-requirements-skill-design.md`
- `docs/superpowers/specs/2026-08-19-architecture-skill-design.md`
- `docs/superpowers/specs/2026-08-19-construction-skill-design.md`

## Propósito

Content pack que cierra el ciclo: toma el sistema ya construido (todas las
Épicas mergeadas a `develop`), identifica qué falta para que el 100% de la
funcionalidad declarada en Requerimientos quede probado — no solo a nivel
unitario (ya cubierto en Construcción vía TDD) — y agrega integración, e2e
sobre los flujos de negocio reales, verificación medible de los NFR
declarados en Arquitectura, y una pasada de seguridad holística que
Construcción no puede ver por trabajar épica a épica.

## No-objetivos

- Reescribir o reemplazar los tests unitarios de Construcción — QA los toma
  como base, no repite ese trabajo.
- Ejecutar el despliegue real — sigue siendo un subsistema aparte, no
  cubierto (ver preguntas abiertas de Construcción).
- Pentesting manual profundo o auditoría de cumplimiento normativo
  específica de industria — la pasada de seguridad acá es automatizada
  (SAST/dependency scanning + escenarios puntuales), no un pentest completo;
  eso, si hace falta, es un pack específico por tipo de proyecto (deferido,
  igual que el resto de packs por tipo de proyecto).

## Qué significa "100% de cobertura" acá (definición operativa)

**No es porcentaje de líneas de código.** Un número de cobertura de líneas
alto puede convivir con comportamiento real sin probar — es exactamente el
tipo de falsa sensación de seguridad que este sistema existe para evitar.

La definición es: **toda HU no retirada de Requerimientos tiene, para cada
uno de sus criterios de aceptación Given/When/Then, al menos un test real
(unitario de Construcción, o integración/e2e de esta fase) referenciado en
la columna "Casos de prueba" de `docs/requirements/traceability.md`.** Es
una verificación mecánica de referencia cruzada, no una métrica estadística
— o está cubierto y trazado, o no lo está.

## Artefactos y ubicación

```
docs/qa/
  plan.md
  qa-report.md
```

El código de test real (integración, e2e, carga/performance, seguridad)
vive en la estructura de tests que el propio stack del proyecto ya tenga
(ej. `tests/integration/`, `tests/e2e/`, según convención del framework
elegido en la ADR de Arquitectura) — QA no inventa su propia carpeta de
tests, igual que Construcción no inventa su propia carpeta de código.

### `plan.md`

Lista de tareas de test, análogo al `EPIC-N-plan.md` de Construcción pero
para toda la fase (no hay fan-out natural por unidad aquí como para
justificar un archivo por tarea — el volumen es menor). Cada tarea:

- `id`: `TEST-N`
- `tipo`: `integration` | `e2e` | `nfr` | `security`
- `cubre`: ids de HU (para `integration`), un `FLUJO-N` (para `e2e`), un
  `NFR-N` (para `nfr`), o `general` (para `security`)
- `depende_de`: ids de otras `TEST-N`, si aplica
- `estado`: pendiente/en progreso/completa/bloqueada

### `qa-report.md`

**Auto-generado, no editar a mano** (mismo criterio que `.factory/board.md`
del núcleo) — regenerado al cerrar la fase con: resumen de cobertura (HU
cubiertas vs total), resultado de verificación de cada NFR (medido vs
objetivo), resumen de hallazgos de seguridad por severidad, y qué flujos de
negocio tienen e2e real corriendo.

## Unidad principal de fan-out: la Épica

QA declara la **Épica** como su unidad principal (mismo mecanismo del
núcleo que Construcción), aunque su pipeline no hace fan-out nativo por
Épica sino por `TEST-N` — el alcance por unidad se resuelve filtrando qué
`TEST-N` corresponden a esa Épica:

1. **Manual**: un paso suelto, con el chequeo de prerequisitos del núcleo.
2. **Automático por unidad**: "corré QA solo de lo que tocó la épica 3" —
   `coverage_gap_analysis` filtra a HU/NFR de `EPIC-3` y a los `FLUJO-N`
   **completamente** contenidos en esa Épica (un flujo que cruza a otra
   Épica queda fuera de este alcance, solo se cubre en modo completo). Crea
   su propia rama `feature/qa-coverage-epic-3-<slug>` y su propio PR,
   independiente de la corrida general.
3. **Automático completo**: "corré QA de todo" — sin filtro, como está
   descrito en el resto de este spec, rama `feature/qa-coverage-<slug>`.

El skill `qa-auditor` (Auditor standalone del núcleo) permite "auditá QA de
la épica 3" (corre `qa_audit` + `qa_integral_audit` sobre lo que ya está
cubierto para esa Épica, sin volver a escribir tests) o "auditoría general
de QA" (mismo par de auditores sobre todo lo cubierto a la fecha).

## Pipeline de ejecución (usa el mecanismo transversal del núcleo)

Cada paso es invocable manualmente con el chequeo de prerequisitos del
núcleo, además del modo automático (por unidad o completo, ver arriba) que
encadena todo hasta `pr_gate`.

```
- id: coverage_gap_analysis [agéntico]
  depende_de: []
  fan_out: null
  paralelizable: false
  # lee traceability.md (qué HU ya tienen test unitario pero no
  # integración/e2e donde corresponda), flujos/FLUJO-N.md (cuáles no
  # tienen e2e todavía), constraints.md (qué NFR-N no tienen verificación
  # real todavía) — arma docs/qa/plan.md con las TEST-N que faltan

- id: qa_branch_setup [mecánico]
  depende_de: [coverage_gap_analysis]
  fan_out: null
  paralelizable: false
  # crea feature/qa-coverage-<slug> desde develop (con todas las Épicas de
  # Construcción ya mergeadas a esta altura)

- id: integration_tests [agéntico]
  depende_de: [qa_branch_setup]
  fan_out: "una instancia por TEST-N de tipo integration"
  paralelizable: true

- id: e2e_tests [agéntico]
  depende_de: [qa_branch_setup]
  fan_out: "una instancia por TEST-N de tipo e2e (una por FLUJO-N sin cobertura)"
  paralelizable: true
  # sigue la secuencia de HU declarada en el FLUJO-N.md correspondiente,
  # usando la navegación real de las pantallas (ya debe honrar el flujo,
  # verificado en Arquitectura)

- id: nfr_tests [agéntico]
  depende_de: [qa_branch_setup]
  fan_out: "una instancia por TEST-N de tipo nfr (una por NFR-N)"
  paralelizable: true
  # corre el test de carga/performance real correspondiente al NFR-N y
  # loguea el valor medido vía factory log audit_evidence (con git_head,
  # mecanismo del núcleo) — no es code review, es medición real

- id: security_tests [agéntico]
  depende_de: [qa_branch_setup]
  fan_out: null
  paralelizable: false
  # pasada única y holística: SAST/dependency scanning sobre todo el
  # sistema integrado, más escenarios de seguridad puntuales que
  # audit_security de Construcción no pudo ver por trabajar épica a épica
  # en aislamiento (ej. un endpoint de una épica combinado con datos de
  # otra puede abrir un camino que ninguna auditoría por-épica ve sola)

- id: traceability_update [mecánico]
  depende_de: [integration_tests, e2e_tests, nfr_tests, security_tests]
  fan_out: null
  paralelizable: false
  # completa la columna "Casos de prueba" de traceability.md con los ids
  # de test reales generados en los pasos anteriores

- id: qa_audit [rol: Auditor]
  depende_de: [traceability_update]
  fan_out: "audit_coverage [mecánico], audit_nfr_compliance [mecánico], audit_test_quality [agéntico], audit_security_findings [agéntico]"
  paralelizable: true
  # las 2 mecánicas no necesitan despacho de agente; las 2 agénticas sí,
  # y corren en paralelo con ellas. Mismo tope de 3 iteraciones compartido
  # del núcleo

- id: qa_integral_audit [rol: Auditor Integral]
  depende_de: [qa_audit]
  fan_out: null
  paralelizable: false
  # último paso agéntico antes del gate: coherencia entre lo que QA probó
  # y lo que Requerimientos/Arquitectura/Construcción declararon

- id: pr_gate [mecánico + pregunta al usuario]
  depende_de: [qa_integral_audit]
  fan_out: null
  paralelizable: false
  # abre PR de feature/qa-coverage-... a develop; pregunta si se aprueba
  # acá o se revisa manualmente — este PR es el gate de aprobación humana
  # de la fase
```

## Checklist del auditor

### `audit_coverage` (mecánico) — la definición operativa de "100%"

1. Toda HU no retirada en `traceability.md` tiene la columna "Casos de
   prueba" no vacía, y cada id referenciado ahí existe como test real en el
   código (no un id inventado que no corresponde a ningún archivo).
2. Todo criterio de aceptación Given/When/Then de cada HU está cubierto por
   al menos un test (no alcanza con que la HU tenga *algún* test si un
   criterio específico quedó sin ejercitar).

### `audit_nfr_compliance` (mecánico)

3. Todo `NFR-N` de `constraints.md` tiene un evento `audit_evidence`
   logueado por `nfr_tests` con `git_head` vigente (mismo mecanismo
   anti-alucinación del núcleo).
4. El valor medido cumple la "Medida de respuesta" declarada — si no la
   cumple, es hallazgo **Bloqueante**, nunca un "se documenta y se sigue".

### `audit_test_quality` (agéntico, semántico)

5. Los tests no son triviales (sin asserts vacíos, sin solo verificar que
   "no explota" cuando la HU exige un comportamiento específico).
6. Los tests de integración/e2e ejercitan comportamiento real de negocio, no
   detalles de implementación que romperían el test ante un refactor válido.
7. Sin patrones frágiles evidentes (esperas por `sleep` fijo en vez de
   esperar la condición real, dependencia de orden de ejecución entre
   tests).

### `audit_security_findings` (agéntico, semántico)

8. Todo hallazgo de `security_tests` tiene severidad asignada
   (Bloqueante/Mayor/Menor, mecanismo del núcleo).
9. Todo hallazgo de severidad Bloqueante pasó por `advisor_block` del
   núcleo — ninguno queda "reportado nomás" sin la confirmación explícita
   que exige el núcleo para riesgo crítico.

### `qa_integral_audit` (rol: Auditor Integral)

i. Todo `FLUJO-N.md` de Requerimientos tiene al menos un test e2e real
   corriendo y pasando (no alcanza con que exista el archivo del test).
ii. Ningún NFR ni flujo quedó "cubierto" solo en `docs/qa/plan.md` sin
   `traceability_update` haberlo reflejado en `traceability.md` — ambos
   documentos deben ser consistentes entre sí.
iii. El sistema integrado en `develop` (con QA ya sumado) sigue siendo
   coherente con las ADR de Arquitectura — ninguna solución de test reveló
   que una decisión arquitectónica no se sostiene en la práctica sin que
   quede documentado como hallazgo a escalar.

## Extensión del CLI del núcleo

`factory validate qa` — corre `audit_coverage` y `audit_nfr_compliance` de
forma determinística sobre `docs/requirements/traceability.md`,
`docs/architecture/constraints.md` y `.factory/log.jsonl`, cruzando además
con el código real de tests. Devuelve lista de problemas (vacía si todo
bien) — mismo patrón que las validaciones de las demás fases.

## Manejo de errores / casos borde

- Un NFR-N no cumple su "Medida de respuesta" al medirlo de verdad: hallazgo
  Bloqueante, se escala al usuario mostrando medido vs objetivo — la
  resolución puede requerir volver a Construcción (optimizar) o a
  Arquitectura (revisar la ADR/el NFR mismo), QA no "arregla" el sistema
  para que el número cierre, solo mide y reporta con honestidad.
- Un `FLUJO-N.md` resulta no recorrible porque la navegación real de
  Arquitectura no lo soporta (se le escapó a la verificación 11 del checklist
  de cierre de Arquitectura): hallazgo bloqueante en `qa_integral_audit`,
  se escala señalando el `FLUJO-N` y el `SCREEN-N` en conflicto — no se
  inventa un camino alternativo sin decírselo al usuario.
- `security_tests` encuentra una vulnerabilidad crítica: `advisor_block`
  del núcleo — el PR no se abre hasta que el usuario confirma
  explícitamente cómo proceder (corregir antes del PR, o aceptar el riesgo
  documentado, nunca un salto silencioso).

## Testing

pytest, cero IO externo real (sin correr suites de test reales del proyecto
objetivo ni herramientas de carga/SAST dentro de los tests del propio
`factorysoftware` — se mockean), fixtures de árbol de documentos en
`tmp_path`:

- `test_validate_qa.py`: caso positivo (traceability 100% cubierta, todos
  los NFR dentro de umbral) y un caso negativo por cada verificación
  mecánica 1–4 (HU sin test referenciado, id de test inventado, criterio
  Given/When/Then sin cubrir, NFR sin evidencia, NFR con valor medido fuera
  de umbral).

## Preguntas abiertas para specs futuros

- Ejecutar el despliegue real, más allá de que QA ya dejó el sistema
  verificado, sigue sin spec — es el subsistema pendiente que cierra el
  ciclo completo pedido originalmente (requerimientos → QA), si se decide
  cubrirlo.
- Packs específicos por tipo de proyecto (pentesting profundo para
  proyectos de seguridad, testing de accesibilidad para frontend, testing
  de automatizaciones/RPA, etc.) quedan fuera de v1, mismo criterio de
  diferimiento que en el núcleo.
