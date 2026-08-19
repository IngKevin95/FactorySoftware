# Núcleo de la Fábrica + Capa de Agnosticismo de Proveedor — Diseño

Estado: aprobado
Subsistema: 1 de N (núcleo) — ver `docs/superpowers/specs/README.md` para el índice completo de la descomposición una vez creado.

## Propósito

Proveer un paquete instalable y agnóstico de proveedor que scaffoldea un
sistema de skills multi-fase de SDLC (requerimientos -> arquitectura/diseño
-> construcción -> QA) dentro de cualquier proyecto de software, adaptado
automáticamente al/los asistente(s) de IA presentes en ese proyecto (Claude
Code, GitHub Copilot, OpenAI Codex CLI, OpenCode, Antigravity), con gestión
completa de ciclo de vida (instalar/actualizar/desinstalar) y trazabilidad y
métricas locales.

Este spec cubre solo el **núcleo**: el instalador, los adaptadores de
proveedor y el mecanismo de estado/trazabilidad. El contenido real de cada
fase (skill de requerimientos, skill de arquitectura, etc.) y los packs por
tipo de proyecto (backend/mobile/seguridad/...) son subsistemas separados con
sus propios specs, construidos sobre este núcleo.

## Prioridad de implementación (v1)

Los 5 adapters se implementan en v1, pero no con el mismo nivel de rigor:

- **Claude Code y Antigravity son los proveedores primarios** — el usuario
  los prueba de inmediato. Sus adapters requieren verificación real del
  formato de instrucciones (no best-effort) y quedan cubiertos por tests de
  `detect()`/`render()` contra fixtures fieles al formato real de cada uno.
  Antigravity en particular necesita investigación activa (búsqueda web)
  antes de escribir el adapter — al ser prioritario, no alcanza con el
  fallback genérico descrito más abajo; si la investigación no encuentra un
  formato confiable, se marca como bloqueante y se avisa antes de continuar,
  en vez de instalar un fallback sin verificar.
- **Copilot, Codex y OpenCode son secundarios** — deben quedar listos y
  funcionales en v1, pero no se prueban de inmediato. Para estos sí aplica
  el criterio "best-effort con fallback marcado como no verificado" descrito
  en la sección de notas por proveedor: se implementan con la mejor
  información disponible, se documenta cualquier supuesto no confirmado, y
  se corrigen después si la prueba real revela diferencias.

## No-objetivos (v1)

- Llamar directamente a ninguna API de LLM. El paquete nunca habla con un
  modelo; solo escribe archivos de instrucciones que un asistente de IA ya en
  ejecución lee.
- Telemetría remota/en la nube. Todos los logs y métricas quedan locales al
  proyecto (`.factory/`), nada se transmite a ningún lado.
- Contenido completo de fases (skills de requerimientos/arquitectura/
  construcción/QA) — esos son specs separados. Este núcleo solo define
  *cómo* ese contenido se renderiza e instala por proveedor.
- Packs específicos por tipo de proyecto (backend, mobile, seguridad,
  automatizaciones, agentes, ...) — diferidos, el núcleo solo define el punto
  de extensión.

## Arquitectura

Paquete Python `factorysoftware`, distribuido vía pip/uv. Tres capas:

1. **Content** — archivos markdown fuente agnósticos de proveedor (un
   archivo por skill, frontmatter YAML para nombre/descripción + cuerpo).
   Única fuente de verdad.
2. **Adapters** — un módulo Python por proveedor. Cada uno sabe detectar el
   proveedor en un proyecto y renderizar/colocar el contenido en el formato y
   ubicación que ese proveedor espera.
3. **CLI + estado** — comandos de ciclo de vida y un log local append-only
   usado para trazabilidad y métricas.

```
src/factorysoftware/
  cli.py                  # init, update, uninstall, status, log
  adapters/
    base.py                # Protocolo ProviderAdapter
    claude_code.py
    copilot.py
    codex.py
    opencode.py
    antigravity.py
    registry.py             # detect() -> list[ProviderAdapter] presentes en el proyecto
  content/                 # *.md fuente, única fuente de verdad
    advisor.md               # persona Asesor: pros/contras honestos durante la decisión
    auditor.md                # persona Auditor: ejecuta los checklists de cada fase
    auditor_integral.md       # persona Auditor Integral: coherencia entre fase actual y la anterior
    requirements.md
    architecture.md
    construction.md
    qa.md
  render.py                 # (content, adapter) -> archivo(s) renderizado(s)
  state.py                  # manifest.json, log.jsonl, metrics.json
tests/
  test_adapters.py
  test_render.py
  test_state.py
  test_cli.py
```

## Interfaz ProviderAdapter

```python
class ProviderAdapter(Protocol):
    name: str

    def detect(self, project_root: Path) -> bool: ...
    def target_paths(self, skill_ids: list[str]) -> dict[str, Path]: ...
    def render(self, skill_id: str, content_md: str) -> str: ...
```

- `detect`: busca huellas del proveedor (`.claude/`, `.github/copilot*`,
  convenciones de `AGENTS.md`, archivos de configuración propios del
  proveedor).
- `target_paths`: mapea cada id de skill a la ruta que ese proveedor espera
  (puede colapsar varios ids de skill en un solo archivo para proveedores de
  archivo único).
- `render`: convierte el contenido markdown compartido al formato que ese
  proveedor espera (forma del frontmatter, envoltura, concatenación).

### Autodetección — comportamiento por defecto, sin configuración

La autodetección **no es opcional ni requiere que el usuario indique qué
proveedor usa**: es el único camino por defecto, para que instalar la fábrica
sea lo más simple posible (un solo comando, cero preguntas en el caso común).

- `registry.detect(project_root)` corre **todos** los adapters contra el
  proyecto y devuelve la lista completa de los que dieron positivo — un
  proyecto con más de un proveedor configurado (ej. Claude Code y Copilot a
  la vez) instala para ambos automáticamente, sin que el usuario tenga que
  pedirlo.
- El flag `--providers claude,copilot` existe solo como *override* explícito
  para casos borde (forzar instalación de un proveedor sin huella detectable
  aún, o limitar la instalación a un subconjunto) — nunca es necesario para
  el uso normal.
- Solo si `detect()` no encuentra ningún proveedor (proyecto nuevo, sin
  ningún asistente configurado todavía) el CLI cae a un prompt interactivo
  como último recurso. Este es el único punto de fricción permitido.
- La detección se re-ejecuta en cada `factory update`, así que si se agrega
  un proveedor nuevo al proyecto después de la instalación inicial, el
  siguiente `update` lo detecta e instala sin pasos manuales adicionales.

### Notas por proveedor (v1, básico)

- **Claude Code**: multi-archivo, `.claude/skills/<id>/SKILL.md`,
  frontmatter YAML `name`/`description`.
- **GitHub Copilot**: archivo único `.github/copilot-instructions.md`,
  concatena todo el contenido de fases con encabezados.
- **OpenAI Codex CLI**: archivo único `AGENTS.md` en la raíz del repo,
  markdown plano, sin frontmatter.
- **OpenCode**: tratado como Codex (convención `AGENTS.md`) para el adapter
  básico v1 — verificar contra la documentación vigente antes de
  implementar, el formato puede diferir.
- **Antigravity**: proveedor primario (ver "Prioridad de implementación"),
  formato no conocido con confianza a partir del conocimiento actual. La
  tarea de implementación empieza con investigación activa (búsqueda web)
  del formato real de instrucciones/skills antes de escribir una sola línea
  del adapter. Si esa investigación no logra confirmar el formato con
  confianza razonable, se detiene y se reporta al usuario en vez de instalar
  un fallback sin verificar — al ser un proveedor que se prueba de
  inmediato, un adapter que escribe en el lugar equivocado es peor que no
  tener adapter.

## Comandos de ciclo de vida

- `factory init`
  Autodetecta proveedores presentes (`registry.detect`, ver sección de
  autodetección arriba) — no requiere ningún argumento en el caso normal.
  Renderiza el contenido vía cada adapter que dio positivo, escribe los
  archivos, registra cada ruta escrita + hash de contenido en
  `.factory/manifest.json`.

- `factory update`
  Vuelve a correr la autodetección (por si se agregó un proveedor nuevo) y
  re-renderiza el contenido desde la versión del paquete actualmente
  instalada. Para cada archivo escrito previamente: si su hash en disco
  todavía coincide con el hash del manifest (no fue tocado por el usuario),
  lo sobreescribe con el nuevo render y actualiza hash + versión en el
  manifest. Si el hash difiere (el usuario lo editó a mano), lo salta e
  imprime una advertencia con el archivo en cuestión — nunca pisa ediciones
  del usuario en silencio.

- `factory uninstall`
  Lee `.factory/manifest.json`, borra exactamente los archivos que lista
  (salta los que ya no coinciden en hash, advierte en vez de borrar), y
  después borra el manifest. Nunca toca archivos que no escribió.

- `factory status [--write]`
  Lee `.factory/log.jsonl` y `.factory/manifest.json`, imprime: versión
  instalada, proveedores detectados, fase actual (del último evento de
  transición de fase), métricas de cobertura de QA, conteo de invocaciones
  por skill. Con `--write`, además regenera `.factory/board.md` (ver
  sección "Tablero de seguimiento" abajo) en vez de solo imprimir por
  stdout.

- `factory log <event_type> [--data '<json>']`
  Agrega una línea a `.factory/log.jsonl`: `{"ts", "event_type", "data"}`.
  Este es el hook que las skills de contenido de cada fase llaman (vía
  Bash/shell, ya que cualquier agente capaz de correr las skills de la
  fábrica puede correr un comando de shell) después de transiciones de fase,
  creación de artefactos y — de forma crítica — desacuerdos del asesor, para
  que las auditorías puedan reconstruir qué pasó y por qué.

## Archivos de estado (`.factory/`, versionados en git por defecto)

- `manifest.json` — `{version, installed_at, providers: [...], files: [{path, hash, skill_id}]}`
- `log.jsonl` — stream de eventos append-only, un objeto JSON por línea
- `metrics.json` — caché calculada (reconstruida desde log.jsonl por
  `factory status`), no se edita a mano
- `board.md` — ver "Tablero de seguimiento" abajo

## Tablero de seguimiento (`.factory/board.md`, transversal)

Seguir el progreso no debe depender de correr un comando y leer texto suelto
cada vez. `factory status --write` regenera `.factory/board.md` — markdown
plano, versionado en git, se ve en cualquier diff/PR/editor sin herramienta
adicional. Se reconstruye 100% desde `.factory/log.jsonl` (nunca se edita a
mano, cualquier edición manual se pierde en la próxima regeneración).

Estructura mínima:

```markdown
# Tablero de la Fábrica (auto-generado, no editar a mano)

## Fase actual: <nombre de fase>

### Requerimientos: ✅ completo | 🟡 en progreso | ⚪ no iniciado
### Arquitectura: ...
### Construcción: ...
### QA: ...

## Detalle de <fase actual, si tiene granularidad por Épica>

| Épica | Depende de | Estado | Paso actual | Auditoría | PR |
|-------|-----------|--------|-------------|-----------|-----|
| EPIC-1 | — | 🟢 en progreso | task_execution (3/4 tareas) | pendiente | — |
| EPIC-2 | EPIC-1 | ⏸️ esperando EPIC-1 | branch_setup bloqueado | — | — |
| EPIC-3 | — | ✅ mergeada | — | ok | #12 (merged) |
```

Toda fase que declare pasos con `fan_out` a nivel de Épica (hoy:
`hu_por_epica` en Requerimientos, `task_planning`/`task_execution`/
`construction_audit`/`pr_gate` en Construcción) alimenta esta tabla — cada
spec de fase indica, al declarar sus pasos, cuáles corresponden a qué
columna. El estado de cada Épica sale de los eventos `pipeline_step`,
`audit_iteration` y `phase_gate` correspondientes a esa Épica en el log; la
columna "Depende de" sale del mecanismo de dependencias entre Épicas que
define el spec de Construcción.

## Comportamiento de bloqueo del asesor/auditor (transversal, definido acá
porque afecta el schema del log)

La persona asesora (spec de contenido, archivo separado) exige que el agente
presente pros/contras y una recomendación honesta en cada decisión
significativa, incluso en desacuerdo con el usuario. Para un conjunto
definido de categorías de riesgo crítico (seguridad, pérdida de datos, tests
saltados en silencio, acciones de infra/deploy irreversibles) la skill
instruye al agente a exigir un paso de confirmación explícita adicional
antes de continuar, y a loguear el desacuerdo vía
`factory log advisor_block '{"category": ..., "reason": ..., "user_override": bool}'`.
Los desacuerdos no críticos se loguean vía `factory log advisor_note` pero no
bloquean.

## Loop auditor-constructor (transversal, aplica a toda fase con gate de
aprobación)

Cada fase que termina en un gate de aprobación humana (ver cada spec de
contenido de fase para su checklist específico) pasa primero por un ciclo de
auditoría automática antes de pedirle al usuario que apruebe:

1. El agente constructor produce/actualiza los artefactos de la fase.
2. Se ejecuta una revisión de auditoría contra el checklist de esa fase
   (coherencia interna, cobertura, ausencia de gaps respecto a la fase
   anterior). Mecanismo de la revisión, en orden de preferencia:
   - Si el proveedor soporta despachar un agente/rol independiente (ej. el
     `Agent` tool de Claude Code con un tipo de agente revisor), se despacha
     ese agente separado para la auditoría — más independencia, no comparte
     el mismo hilo de razonamiento que produjo el artefacto.
   - Si el proveedor no soporta subagentes, el mismo agente ejecuta un paso
     de autocrítica estructurada, explícitamente separado del paso de
     construcción (no se mezclan en el mismo razonamiento continuo).
3. Si la auditoría encuentra hallazgos, se corrigen y se vuelve al paso 1.
4. El loop tiene un tope de **3 iteraciones**. Si al llegar a la tercera
   todavía hay hallazgos sin resolver, el agente detiene el loop y escala al
   usuario mostrando qué quedó pendiente y por qué — nunca loopea indefinido
   ni se "auto-aprueba" por cansancio del ciclo.
5. Cada iteración del loop se registra vía
   `factory log audit_iteration '{"phase": ..., "role": "auditor"|"auditor_integral", "iteration": N, "findings": [...]}'`
   (el campo `role` distingue si el hallazgo vino del Auditor de fase o del
   Auditor Integral), y el resultado final (aprobado / escalado) vía
   `factory log phase_gate '{"phase": ..., "result": "approved"|"escalated", "iterations": N}'`.
6. Pasar la auditoría automática es condición necesaria pero no suficiente
   para avanzar de fase — el gate de aprobación humana explícita (definido
   por cada spec de fase) sigue aplicando después de que el loop cierra
   limpio.

## Dos roles de auditoría (transversal, obligatorio en toda fase)

El "loop auditor-constructor" de la sección anterior no es un solo rol
difuso — son dos roles distintos, cada uno con su propia persona de
contenido (`content/auditor.md`, `content/auditor_integral.md`), separados
del Asesor (`content/advisor.md`, que opina *durante* la construcción de un
artefacto) y del agente constructor:

1. **Auditor** (`content/auditor.md`) — corre el checklist de **una sola
   fase**, contra su propio criterio de completitud/coherencia interna (ej.
   el checklist de `adrs_audit` o el cierre de Requerimientos). Es el que
   ejecuta las iteraciones 1–3 del loop descrito arriba dentro de esa fase.
2. **Auditor Integral** (`content/auditor_integral.md`) — corre **después**
   de que el Auditor de fase cierra limpio, y valida coherencia **entre la
   fase que cierra y la fase anterior que le dio origen**: lee el conjunto
   completo de documentos de ambas fases (no solo cruza ids mecánicamente,
   ya cubierto por el checklist estructural de cada fase) y verifica que
   ningún objetivo/métrica de éxito de la fase anterior quedó silenciosamente
   sin cubrir, y que la fase que cierra no introdujo alcance sin respaldo en
   la fase anterior (scope creep). Obligatorio en toda fase que tenga una
   fase previa de la que depender — Requerimientos no lo necesita (es la
   primera fase), Arquitectura sí (contra Requerimientos), Construcción sí
   (contra Arquitectura), QA sí (contra Construcción).

Ambos roles se despachan siguiendo la misma regla del núcleo: agente
independiente si el proveedor lo soporta, autocrítica estructurada si no. El
Auditor Integral corre como el último paso agéntico antes del gate de
aprobación humana de cada fase — después de él, ya no hay más auditoría
automática, solo la decisión del usuario.

## Pipeline de pasos agénticos (transversal, obligatorio en todo proveedor)

Ninguna fase se ejecuta como una sola pasada monolítica. Cada spec de
contenido de fase debe declarar su trabajo como una secuencia de **pasos**
con dependencias explícitas, y algunos pasos pueden tener **fan-out**
(múltiples instancias independientes del mismo paso, una por elemento de una
colección — ej. "una HU por cada Épica"). Esto es obligatorio en los 5
proveedores, no una optimización opcional: el valor no es solo eficiencia de
tokens, es que cada paso queda como una unidad de trabajo separada, auditable
y con contexto acotado (un agente que solo redacta las HU de una épica nunca
carga en su contexto las HU de las otras épicas).

### Declaración de pasos

Cada spec de fase incluye una lista de pasos con esta forma:

```
- id: <nombre>
  depende_de: [<ids de pasos previos>] | []
  fan_out: null | "<descripción de la colección a iterar>"
  paralelizable: true | false
```

Un paso con `fan_out` no nulo y `paralelizable: true` es candidato a
despacharse como N instancias independientes en paralelo — pero solo si el
paso además es semánticamente independiente entre elementos (dos instancias
del mismo paso no deben necesitar verse entre sí para producir un resultado
coherente; si lo necesitan, `paralelizable: false` aunque tenga fan-out, y se
ejecuta en serie, una instancia a la vez).

### Regla de despacho (la misma en los 5 proveedores)

1. Si el proveedor soporta despachar agentes/subagentes independientes con
   ejecución concurrente (ej. el `Agent` tool de Claude Code lanzando varias
   invocaciones en un mismo mensaje), los pasos `paralelizable: true` con
   fan-out se despachan como un agente independiente por instancia,
   corriendo en paralelo.
2. Si el proveedor no soporta despacho concurrente de subagentes, el mismo
   paso se ejecuta igual — instancia por instancia — pero en serie, dentro
   de la misma sesión o invocando el mecanismo de subagente síncrono que el
   proveedor tenga, uno a la vez.
3. Pasos sin fan-out o marcados `paralelizable: false` siempre se ejecutan
   como un único paso, respetando el orden de `depende_de` (nunca arranca un
   paso antes de que todos sus `depende_de` hayan cerrado).
4. Cada paso, y cada instancia de un paso con fan-out, se loguea al empezar
   y al terminar vía
   `factory log pipeline_step '{"phase": ..., "step_id": ..., "fan_out_index": ...|null, "mode": "parallel"|"serial", "estado": "iniciado"|"completado"}'`
   — así `factory status` puede reconstruir qué modo de ejecución se usó
   realmente en cada corrida, útil para comparar eficiencia entre
   proveedores.

## Modos de invocación: manual y automático (transversal, obligatorio en
toda fase)

Todo paso declarado debe poder invocarse de dos formas — nunca solo una:

1. **Manual (paso suelto)**: el usuario le pide al agente ejecutar un paso
   puntual (ej. "generá el PRD", "armá las HU de la épica 2"). El agente
   ejecuta *solo* ese paso.
2. **Automático (flujo completo)**: el usuario le pide correr la fase
   entera. El agente encadena todos los pasos declarados en orden de
   `depende_de` (respetando fan-out y la regla de despacho de arriba) y
   termina con el Auditor de fase + el Auditor Integral + el gate — sin
   pararse a esperar confirmación entre pasos intermedios.

### Contrato de invocación manual: no se salta prerequisitos en silencio

Antes de ejecutar un paso puntual, el agente **debe** verificar que todos
sus `depende_de` estén completos:

1. Consulta `.factory/log.jsonl` (vía `factory status --step <phase>.<step_id>`,
   ver extensión del CLI abajo) buscando el último evento `pipeline_step`
   de cada dependencia con `estado: completado` (y, si la dependencia tiene
   fan-out, que **todas** sus instancias estén completas).
2. Si falta alguna dependencia, el agente **no ejecuta el paso pedido**.
   En su lugar, le informa al usuario cuál(es) paso(s) previo(s) falta(n) y
   **sugiere explícitamente ejecutarlo(s) primero** (vía `AskUserQuestion` o
   el equivalente del proveedor) — nunca lo ejecuta de forma automática sin
   preguntar, y nunca lo ignora silenciosamente y sigue con el paso pedido
   sobre datos incompletos.
3. Si el usuario confirma, el agente corre la(s) dependencia(s) faltante(s)
   primero y encadena hacia el paso originalmente pedido. Si el usuario
   dice que no, el agente se detiene y no ejecuta nada.

Este chequeo aplica también dentro del modo automático de forma implícita
(el orden de `depende_de` ya lo garantiza), pero el contrato explícito de
arriba es solo necesario para el modo manual, donde el usuario puede pedir
cualquier paso en cualquier orden.

### Exposición por proveedor

- **Proveedores multi-archivo (Claude Code)**: cada fase se renderiza como
  un skill orquestador (`<phase>/SKILL.md`, modo automático) más un skill
  por paso declarado (`<phase>-<step_id>/SKILL.md`, modo manual, con el
  contrato de verificación de prerequisitos incluido en sus instrucciones).
  `render.py` deriva ambos a partir del mismo contenido fuente: el `.md` de
  cada fase se estructura con un heading `## Paso: <step_id>` por paso
  declarado — el skill manual de un paso es el preámbulo de la fase + esa
  sección; el skill automático es el preámbulo + todas las secciones
  concatenadas en orden + la instrucción de encadenarlas.
- **Proveedores de archivo único (Copilot, Codex, OpenCode, Antigravity)**:
  no hay separación física de archivos — el único archivo de instrucciones
  incluye ambos modos como contenido: instrucciones de cómo ejecutar la
  fase completa, y por separado, para cada paso, sus instrucciones más el
  contrato de verificación de prerequisitos. El agente decide qué parte
  aplicar según lo que el usuario pidió.

### Extensión del CLI del núcleo

`factory status --step <phase>.<step_id> [--fan-out-index N]` — devuelve
`completado` o `pendiente` consultando el último evento `pipeline_step`
correspondiente en `.factory/log.jsonl` (agregando sobre todas las
instancias de fan-out si no se especifica índice). Es el mecanismo que
respalda el contrato de invocación manual de arriba — determinístico, no
depende del juicio del agente para saber si algo ya se corrió.

## Manejo de errores

- `update`/`uninstall` nunca borran ni sobreescriben un archivo cuyo hash no
  coincide con el manifest — siempre advierten y saltan en su lugar.
- `init` corrido dos veces en un proyecto ya instalado: se detecta como "ya
  instalado" (existe manifest) — se comporta como `update`, no como una
  instalación duplicada.
- Falta `.factory/manifest.json` al correr `update`/`uninstall`/`status`:
  error claro pidiendo correr `init` primero.
- `detect()` de un adapter lanza excepción o una ruta destino no es
  escribible: ese proveedor se salta con una advertencia, los demás
  proveedores detectados siguen adelante (una instalación parcial es válida
  y queda registrada en el manifest).

## Testing

pytest + pytest-mock, cero IO externo (sin red real, sin registries de
paquetes reales). Operaciones de filesystem ejercitadas vía `tmp_path`. Según
las reglas de Beck:

- `test_adapters.py`: un test por adapter para `detect()` (fixtures de
  árbol de proyecto positivos/negativos) y `render()` (snapshot del output
  renderizado).
- `test_render.py`: contenido -> renderizado multi-proveedor produce el
  conjunto de archivos esperado.
- `test_state.py`: tracking de hash del manifest, invariante append-only del
  log, agregación de métricas desde un log fixture.
- `test_cli.py`: idempotencia de init/update/uninstall y específicamente el
  comportamiento de "no pisar ediciones del usuario" (es la única rama no
  trivial de todo el sistema — tiene test dedicado).
- `test_board.py`: `factory status --write` sobre un `log.jsonl` fixture con
  eventos de varias fases/Épicas produce el `.factory/board.md` esperado
  (snapshot); regenerar sobre un `board.md` editado a mano lo sobreescribe
  sin preguntar (documentado como comportamiento esperado, no un bug).

## Preguntas abiertas / riesgos marcados para el plan de implementación

- La convención real de carga de skills de Antigravity necesita
  verificación por búsqueda web antes de implementar ese adapter de verdad —
  no fabricar el formato.
- La convención actual de OpenCode también debe confirmarse, no asumirse
  idéntica a la de Codex.
