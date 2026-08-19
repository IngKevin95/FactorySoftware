# Skill de Construcción — Diseño

Estado: aprobado
Subsistema: 4 de N (fase de contenido: Construcción) — depende del núcleo,
Requerimientos y Arquitectura:
- `docs/superpowers/specs/2026-08-19-factory-core-design.md`
- `docs/superpowers/specs/2026-08-19-requirements-skill-design.md`
- `docs/superpowers/specs/2026-08-19-architecture-skill-design.md`

## Propósito

Content pack que toma los contratos congelados de Arquitectura (ADRs,
`data-model.md`, `API-N.md`, `SCREEN-N.md`) y las HU de Requerimientos, y
construye el código real, épica por épica, con planificación de tareas por
rol (catálogo base + condicional: frontend/backend/data, más seguridad/
automatizaciones/mobile según lo que cada HU dispare), ejecución paralela
aislada por rama/worktree, TDD por tarea con gate mecánico de verificación,
auditoría por 4 dimensiones independientes (funcionalidad, buenas
prácticas, seguridad, eficiencia), y gate de aprobación vía Pull Request
siguiendo el Git Flow del proyecto.

## No-objetivos

- Tests de integración/e2e y auditoría de cobertura total — fase de QA (spec
  futuro), que toma el código + los `API-N.md`/`SCREEN-N.md` como su propio
  contrato a validar.
- Redefinir contratos de Arquitectura o alcance de Requerimientos — son
  inputs de solo lectura.
- Ejecutar el despliegue real (el "cómo desplegar" ya quedó decidido como
  ADR en Arquitectura; ejecutar ese despliegue en un entorno real es un
  subsistema aparte, no cubierto todavía — ver preguntas abiertas).

## Convención de Git asumida (flag de diseño)

Este spec asume Git Flow (`feature/<slug>` desde `develop`, merge a
`develop` vía PR con merge commit `--no-ff`, nunca squash/rebase) porque es
la convención declarada en el `CLAUDE.md` de este usuario. Un proyecto que
use otra convención (trunk-based, GitHub flow simple) necesitaría que este
paso lea la convención real del proyecto en vez de asumir Git Flow siempre
— queda como pregunta abierta para cuando la fábrica se use en un proyecto
sin esa convención declarada; v1 la asume fija.

## Artefactos y ubicación

```
docs/construction/
  plan/
    EPIC-1-plan.md
    EPIC-2-plan.md
    ...
```

El código real vive en el árbol normal del proyecto (`src/`, o la
convención que el propio proyecto/stack ya tenga) — Construcción no inventa
una carpeta propia para el código, solo para los planes de tareas.

### `plan/EPIC-N-plan.md`

Frontmatter: `id` (`EPIC-N`), `estado`. Cuerpo: lista de tareas.

Cada tarea:
- `id`: `TASK-N.M`
- `rol`: ver catálogo de roles abajo
- `implementa`: ids de `API-N`/`SCREEN-N`/entidad de `data-model.md` que
  esta tarea construye
- `depende_de`: ids de otras `TASK-N.M` (dentro o fuera de la misma épica)
- `descripcion`: qué hace concretamente
- `estado`: pendiente/en progreso/completa/bloqueada

### Catálogo de roles de construcción (por slice)

`task_planning` arma cada slice (una HU que toca pantalla + endpoint + dato)
con este catálogo, no roles libres:

**Base — aparecen cuando la HU toca esa capa:**
- `backend`: implementa el `API-N.md` (lógica de negocio, validaciones,
  persistencia).
- `data`: migración/schema de la entidad en `data-model.md`. Se fusiona con
  `backend` en la misma tarea si el cambio de datos es trivial (un campo);
  se separa en tarea propia si no lo es (así puede correr en paralelo
  mientras `backend` escribe la lógica contra el contrato ya conocido).
- `frontend`: refina el prototipo de `SCREEN-N.md` (rama
  `architecture/ui-prototype`) a producción y lo conecta a la API.

**Condicionales — solo si la HU concreta los dispara, no en cada slice:**
- `seguridad`: la HU toca autenticación, autorización o datos sensibles.
- `automatizaciones`: hay jobs async, integraciones externas, webhooks.
- `mobile`: el proyecto tiene cliente mobile y la HU lo requiere.

Este catálogo cubre **quién construye**. Quién **audita** lo construido es
un catálogo distinto — ver "Auditoría por dimensión" más abajo. La
coordinación de Git (ramas, worktrees, PR) no es un rol agéntico: son los
pasos mecánicos `branch_setup`/`worktree_integration`/`pr_gate` del
pipeline, comandos de git determinísticos sin necesidad de juicio de un
agente.

## Rama y aislamiento de trabajo paralelo

- Una rama `feature/EPIC-N-<slug>` por Épica. Se crea desde
  `architecture/ui-prototype` si esa rama existe y fue aprobada en
  Arquitectura (así las tareas de rol `frontend` refinan el prototipo real
  en vez de reescribirlo desde cero); si no existe (proyecto sin pantallas,
  o fase de Arquitectura anterior a que este paso existiera), se crea desde
  `develop` directamente.
- Las tareas de una misma épica que el plan marca como independientes entre
  sí (sin relación de `depende_de`) se ejecutan en **git worktrees**
  aislados (mecanismo estándar de Git, sin herramienta adicional — ver
  `superpowers:using-git-worktrees`), cada uno arrancando desde el estado
  actual de `feature/EPIC-N-<slug>`. Al terminar, cada worktree se integra
  (merge local, sin squash) a la rama de la épica antes de auditar el
  resultado combinado.
- Tareas con dependencia real (ej. la tarea de backend que expone el
  endpoint antes que la tarea de frontend que lo consume) corren en serie,
  en el mismo worktree o directo en la rama de la épica.

## Frontera con QA: TDD dentro de Construcción

Cada tarea de código entrega **código + sus tests unitarios**, ciclo
red-green-refactor (coherente con las reglas de Beck ya vigentes en el
proyecto: "Passes Tests" es la primera regla). Construcción es responsable
de que la unidad que construye tenga su propia red de tests unitarios antes
de darse por completa. QA (fase futura) no reescribe estos tests; los toma
como base y agrega integración, e2e, y la auditoría de cobertura total
contra `traceability.md`.

**El gate de TDD es doble, no confía solo en lo que el agente reporta**: el
agente que ejecuta `task_execution` hace el ciclo rojo-verde-refactor él
mismo, en línea, mientras construye. Pero que un agente *diga* "los tests
pasan" no es prueba — por eso `audit_functionality` (ver "Auditoría por
dimensión" más abajo) vuelve a correr el test runner real del proyecto y
revisa su exit code de forma mecánica, dentro de `construction_audit`. Un
agente que se equivoca o miente sobre el estado de los tests queda
atrapado ahí, no llega al PR.

## Pipeline de ejecución (usa el mecanismo transversal del núcleo)

Cada paso es invocable manualmente (ej. "planificá solo la épica 3") con el
chequeo de prerequisitos del núcleo — pedir `task_execution` sin
`branch_setup` completo no ejecuta nada, informa qué falta y sugiere
correrlo primero — además del modo automático que encadena todo hasta
`pr_gate`.

Los pasos marcados "mecánico" son determinísticos (comandos de git/test
runner, sin necesidad de juicio de un agente) y se ejecutan como tool calls
directos, no requieren despacho de subagente aunque tengan fan-out. Los
marcados "agéntico" sí requieren razonamiento y siguen la regla de despacho
del núcleo (subagente paralelo si el proveedor lo soporta, serie si no).

```
- id: task_planning [agéntico]
  depende_de: []
  fan_out: "una instancia por cada Épica no retirada de Requerimientos"
  paralelizable: true
  # cada instancia solo ve las HU de su propia épica y los API-N/SCREEN-N
  # que las implementan — arma el grafo de tareas por rol

- id: plan_audit [agéntico, rol: Auditor]
  depende_de: [task_planning]
  fan_out: null
  paralelizable: false
  # ve TODOS los planes de épica juntos — necesario para detectar
  # conflictos entre épicas (ej. dos épicas tocando la misma entidad de
  # datos al mismo tiempo), algo que ninguna instancia aislada del paso
  # anterior puede ver por sí sola

- id: plan_integral_audit [agéntico, rol: Auditor Integral]
  depende_de: [plan_audit]
  fan_out: null
  paralelizable: false
  # valida los planes contra Arquitectura completa: todo ADR/API/pantalla
  # relevante queda cubierto por al menos una tarea, ninguna tarea inventa
  # trabajo sin respaldo en un API-N/SCREEN-N/entidad real (ver checklist)

- id: branch_setup [mecánico]
  depende_de: [plan_integral_audit]
  fan_out: "una instancia por Épica con plan aprobado"
  paralelizable: true
  # crea feature/EPIC-N-<slug> desde architecture/ui-prototype si existe,
  # si no desde develop

- id: task_execution [agéntico]
  depende_de: [branch_setup]
  fan_out: "una instancia por TASK-N.M, respetando depende_de del plan de su épica"
  paralelizable: true
  # código + tests unitarios (TDD) por tarea, en worktree aislado cuando es
  # paralelizable con otras tareas de la misma épica

- id: worktree_integration [mecánico]
  depende_de: [task_execution]
  fan_out: "una instancia por Épica"
  paralelizable: true
  # merge de los worktrees de tareas completas a la rama de la épica

- id: audit_triage [mecánico]
  depende_de: [worktree_integration]
  fan_out: "una instancia por Épica"
  paralelizable: true
  # decide determinísticamente (por patrones de archivo/diff, no juicio de
  # LLM) qué dimensiones de construction_audit se disparan para esa épica.
  # audit_functionality y audit_practices SIEMPRE se disparan (el gate de
  # TDD y la revisión de buenas prácticas no son opcionales para código
  # nuevo). audit_security se dispara si el diff toca archivos de auth/
  # autorización, agrega manejo de input externo nuevo, o el plan de la
  # épica tiene alguna TASK-N.M de rol `seguridad`. audit_efficiency se
  # dispara si el diff agrega loops anidados, queries nuevas, o supera un
  # umbral simple de complejidad ciclomática. La decisión (qué se disparó y
  # por qué se excluyó lo que no) se loguea vía
  # `factory log audit_triage '{"epic": ..., "dimensiones": [...], "excluidas": {...}}'`
  # — saltear una dimensión queda trazable, nunca es un salto silencioso.

- id: construction_audit [agéntico, rol: Auditor]
  depende_de: [audit_triage]
  fan_out: "una instancia por dimensión activada en audit_triage para esa Épica"
  paralelizable: true
  # las dimensiones activas son independientes entre sí (revisar seguridad
  # no necesita ver el resultado de revisar eficiencia) — corren en
  # paralelo cuando el proveedor lo soporta, ver "Auditoría por dimensión"
  # abajo. El tope de 3 iteraciones del núcleo es compartido entre las
  # dimensiones activas: si cualquiera encuentra hallazgos, se corrige y
  # todas las activas vuelven a correr juntas como la siguiente iteración
  # — no 3 iteraciones por dimensión.

- id: construction_integral_audit [agéntico, rol: Auditor Integral]
  depende_de: [construction_audit]
  fan_out: "una instancia por Épica"
  paralelizable: true
  # última pasada antes del PR: el código de la épica sigue fiel a la
  # intención de negocio de sus HU y a las decisiones de las ADR que le
  # aplican, no solo a la letra del contrato técnico (ver checklist)

- id: pr_gate [mecánico + pregunta al usuario]
  depende_de: [construction_integral_audit]
  fan_out: "una instancia por Épica"
  paralelizable: true
  # abre PR de feature/EPIC-N-... a develop (merge commit, --no-ff);
  # pregunta al usuario si lo aprueba acá o lo revisa manualmente — ESTE
  # PR es el gate de aprobación humana de la fase, no un paso aparte
```

## Checklist del auditor

### `plan_audit`

Estructurales (mecánicas):

1. Toda `TASK-N.M` en `implementa` referencia un `API-N`/`SCREEN-N`/entidad
   real de `data-model.md`.
2. Sin referencias circulares en `depende_de`, ni dentro de una épica ni
   entre épicas.
3. Todo `rol` usado es coherente con el stack elegido en las ADR de
   Arquitectura (ej. no aparece `mobile` si ninguna ADR contempla una app
   móvil).

Semánticas:

4. Ninguna tarea de una épica entra en conflicto de escritura concurrente
   sobre la misma entidad/migración con una tarea de otra épica que corre en
   paralelo (si lo detecta, se fuerza una dependencia explícita entre ambas
   o se escala).
5. Granularidad de tareas razonable según Beck (Fewest Elements): ninguna
   tarea está fragmentada en abstracciones prematuras, ninguna tarea agrupa
   responsabilidades no relacionadas.

### `construction_audit` — auditoría por dimensión

Las 4 dimensiones son sub-auditorías independientes, cada una con su propio
checklist, todas bajo el rol Auditor (ver núcleo). `audit_triage` decide
cuáles se disparan para cada épica (`audit_functionality` y
`audit_practices` siempre; `audit_security`/`audit_efficiency` solo si el
diff real lo amerita — ver el paso `audit_triage` en el pipeline). Las
dimensiones activas corren en paralelo (fan-out) cuando el proveedor lo
soporta; los hallazgos de cualquiera de ellas cuentan igual para el tope de
3 iteraciones compartido.

#### `audit_functionality` — el código hace lo que la HU pide

Estructurales (mecánicas):

1. Todos los tests unitarios de la épica pasan (se corre el test runner
   real del stack, no se infiere — este es el chequeo mecánico del gate de
   TDD descrito arriba).
2. Toda `TASK-N.M` del plan de la épica tiene cambios de código
   correspondientes (sin tareas marcadas completas sin diff real).
3. `traceability.md` de Requerimientos queda con una columna "Implementado"
   marcada para toda HU cubierta por esta épica.

Semánticas:

4. El código respeta el contrato congelado de cada `API-N.md`/`SCREEN-N.md`
   sin drift silencioso (si el código necesita desviarse del contrato, eso
   es un hallazgo que se escala, no un ajuste que se hace y se documenta
   después).
5. Un lector humano reconocería el criterio de aceptación Given/When/Then de
   cada HU cumplido en el comportamiento real, no solo en que los tests
   pasan (un test mal escrito puede pasar sin probar nada útil).

#### `audit_practices` — buenas prácticas, aplicando la escalera del `CLAUDE.md` del proyecto

Semántica, en este orden — se detiene en el primer nivel que ya resuelve el
caso, igual que la regla del propio `CLAUDE.md`:

6. **Reglas de Beck (filtro primario)**: Passes Tests (ya cubierto por
   `audit_functionality`), Reveals Intention, No Duplication, Fewest
   Elements — sin interfaces/clases abstractas sin una segunda
   implementación real.
7. **SOLID + GRASP**, solo si la lógica de la tarea realmente lo amerita
   (no se exige forzar principios donde el código simple ya alcanza).
8. **Patrones de diseño (GoF)**, solo si resuelven un problema concreto y
   recurrente presente en el código — nunca forzados porque "es lo
   correcto" en abstracto.
9. **Detección de sobreingeniería** (el sentido inverso de 6–8): abstracción
   sin segunda implementación real, capa de indirección que nadie necesita
   todavía, config para un valor que nunca cambia, patrón aplicado sin un
   problema recurrente real detrás. Un hallazgo acá no es "está mal
   escrito", es "hay más código del que el problema pedía" — el auditor
   debe poder señalar la simplificación concreta, no solo objetar.

#### `audit_security` — seguridad de lo que esta épica construyó

10. Validación de entradas en todo punto que cruza un límite de confianza
    (request de API, input de formulario) — ninguna confía ciegamente en
    datos externos.
11. Autenticación/autorización correcta si la HU la requiere (según el
    anexo funcional de Requerimientos y el contrato de `API-N.md`).
12. Sin secretos/credenciales hardcodeados ni expuestos en logs.
13. Ninguna acción de riesgo crítico (seguridad, pérdida de datos, acciones
    irreversibles) se tomó sin pasar por el mecanismo `advisor_block` del
    núcleo.

#### `audit_efficiency` — uso idiomático del stack y costo por función

14. El código usa el framework/stack elegido en la ADR de forma idiomática
    (no reimplementa a mano algo que el framework ya resuelve, no "pelea"
    contra sus convenciones).
15. Complejidad y costo razonables por función respecto al problema real que
    resuelve (sin recorridos redundantes evidentes, sin problema N+1 de
    queries, sin trabajo repetido que se pudo cachear/evitar con una
    solución simple) — un hallazgo acá viene con la alternativa concreta
    más eficiente, no solo la objeción.

### `plan_integral_audit` (rol: Auditor Integral, contra Arquitectura)

i. Todo `API-N`/`SCREEN-N`/entidad de `data-model.md` relevante para las
   épicas en curso queda cubierto por al menos una `TASK-N.M` — un contrato
   de Arquitectura sin ninguna tarea que lo construya es un hallazgo
   bloqueante.
ii. Ninguna tarea planifica trabajo que no está respaldado por un
   `API-N`/`SCREEN-N`/entidad/ADR real (alcance inventado en la
   planificación).
iii. Las ADR fundacionales (stack, artefactos/método de despliegue) están
   reflejadas en cómo se plantean las tareas (ej. si la ADR de despliegue
   elige contenedores, ninguna tarea asume un modelo de despliegue
   distinto).

### `construction_integral_audit` (rol: Auditor Integral, contra Arquitectura + Requerimientos)

iv. El código de la épica sigue siendo fiel a la intención de negocio de
   cada HU que implementa (no solo pasa los tests, sino que un lector
   humano reconocería el criterio de aceptación Given/When/Then cumplido en
   el comportamiento real).
v. Ninguna ADR quedó parcialmente aplicada (ej. la ADR de despliegue exige
   configuración de contenedor y el código no la incluye).
vi. No hay funcionalidad construida que no esté respaldada por ninguna HU
   ni ADR (scope creep en código, no solo en documentación).

## Extensión del CLI del núcleo

`factory validate construction [--epic EPIC-N] [--dimension functionality|security|...]`
— corre las verificaciones estructurales de `plan_audit` y de las dimensiones
de `construction_audit` que `audit_triage` haya activado (incluyendo correr
el test runner real del proyecto y revisar su exit code para
`audit_functionality`), cruzando `docs/construction/plan/` con
`docs/architecture/` y `docs/requirements/traceability.md`.

`factory audit-triage --epic EPIC-N` — expone la misma heurística
determinística de `audit_triage` como comando aislado, para que el usuario
pueda ver/cuestionar qué dimensiones se activaron para una épica sin tener
que leer el log completo.

## Manejo de errores / casos borde

- Una tarea no logra pasar de rojo a verde tras varios intentos: retry
  acotado a 3 intentos dentro de la tarea misma (mismo tope que el loop de
  auditoría del núcleo); si sigue en rojo, esa tarea queda `bloqueada` y se
  escala sin frenar las demás tareas independientes de la misma épica.
- Conflicto real al integrar un worktree a la rama de la épica: señal de que
  `plan_audit` no detectó una dependencia real entre esas tareas — se trata
  como hallazgo retroactivo de auditoría (se loguea, se corrige la
  dependencia en el plan, no se resuelve el conflicto "a ciegas" con
  `git merge -X ours` ni similar).
- El código necesita desviarse de un contrato ya aprobado en Arquitectura:
  hallazgo bloqueante de `audit_functionality` (verificación 4), se escala
  con la propuesta de cambio de contrato — no se cambia `API-N.md` desde
  Construcción sin que quede como decisión explícita y trazable.
- `audit_practices` encuentra sobreingeniería (verificación 9) pero
  `audit_functionality` no encuentra nada: la épica igual queda bloqueada
  para esa iteración — las dimensiones activas deben cerrar limpio, no
  alcanza con que la funcionalidad esté bien si el código quedó
  sobre-diseñado.
- `audit_triage` decide incorrectamente excluir `audit_security` en una
  épica que sí tocaba datos sensibles (heurística de diff falló): al no ser
  perfecta, la heurística es intencionalmente conservadora — cualquier
  archivo bajo una ruta típica de auth/permisos, o cualquier `TASK-N.M` de
  rol `seguridad` en el plan, fuerza la activación aunque el diff parezca
  menor. Si aun así se escapa un caso, queda registrado en el log con la
  decisión tomada, así es auditable después.

## Testing

pytest, cero IO externo real (sin correr git/test-runners reales del
proyecto objetivo dentro de los tests del propio `factorysoftware` — se
mockean), fixtures de árbol de documentos en `tmp_path`:

- `test_validate_construction.py`: casos positivos y un caso negativo por
  cada verificación estructural de `plan_audit` (1–3) y de `audit_functionality`
  (1–3, la única de las 4 dimensiones con checks estructurales mecánicos —
  `audit_practices`/`audit_security`/`audit_efficiency` son 100% semánticas,
  no tienen contraparte determinística que testear acá).
- `test_audit_triage.py`: por cada heurística de activación (diff toca ruta
  de auth, plan tiene `TASK-N.M` de rol `seguridad`, diff agrega loop
  anidado/query nueva) un caso que confirma que activa la dimensión
  correspondiente, y un caso donde ninguna heurística aplica y
  `audit_security`/`audit_efficiency` quedan correctamente excluidas.

## Preguntas abiertas para specs futuros

- Ejecutar el despliegue real (más allá de la ADR de método/artefactos) no
  está cubierto — si se necesita, es un subsistema aparte.
- Detectar la convención de Git real del proyecto en vez de asumir Git Flow
  fijo queda pendiente si la fábrica se usa en un proyecto con otra
  convención.
- QA (próximo spec) debe definir cómo consume `docs/construction/plan/` y el
  código resultante para armar sus propios casos de integración/e2e, y cómo
  cierra la columna de cobertura total en `traceability.md`.
