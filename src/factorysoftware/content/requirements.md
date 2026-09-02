---
id: requirements
steps:
  - id: prd
    depende_de: []
    fan_out: null
    paralelizable: false
  - id: project_memory_setup
    depende_de: [prd]
    fan_out: null
    paralelizable: true
  - id: epics
    depende_de: [prd]
    fan_out: null
    paralelizable: false
  - id: hu_por_epica
    depende_de: [epics]
    fan_out: "una instancia por cada EPIC-N creada en el paso anterior"
    paralelizable: true
  - id: traceability
    depende_de: [hu_por_epica]
    fan_out: null
    paralelizable: false
  - id: flujos
    depende_de: [hu_por_epica]
    fan_out: null
    paralelizable: false
  - id: audit_loop
    depende_de: [traceability, flujos]
    fan_out: null
    paralelizable: false
---

Content pack de la fábrica que guía al agente para producir el conjunto de documentos de Requerimientos de un proyecto: PRD, Épicas, Historias de Usuario (HU), Flujos de negocio y una matriz de trazabilidad. Este conjunto es el norte funcional de todo el proyecto — Construcción y QA se validan contra él, no al revés. Ningún detalle técnico (contratos de API, diseño de pantallas, arquitectura) se define acá; eso es responsabilidad de la fase de Arquitectura.

## Paso: prd

### Paso 1: prd — PRD.md

Produce `docs/requirements/PRD.md`. Primer paso del pipeline de requerimientos; sin prerequisitos.

## Verificacion de prerequisitos

- Si `docs/requirements/PRD.md` ya existe: preguntar al usuario si desea sobrescribirlo antes de continuar.

## Output esperado

Archivo `docs/requirements/PRD.md` con estas secciones en orden (sin detalle tecnico - sin nombres de tablas, verbos HTTP ni componentes de UI):

1. **Problema** - Que dolor o necesidad resuelve el sistema.
2. **Objetivo de negocio** - Una frase que describe el resultado deseado.
3. **Alcance**
   - **Que entra** - Lista explicita de capacidades incluidas.
   - **Que no entra** - Lista explicita de exclusiones.
4. **Metricas de exito** - Como se mide que el proyecto fue exitoso.
5. **Stakeholders** - Quienes tienen interes en el resultado.
6. **Restricciones conocidas** - Tiempo, presupuesto, tecnologia, regulaciones.
7. **Supuestos** - Que se asume como verdadero para que el alcance tenga sentido.

## Pasos

- [ ] Preguntar al usuario por el contexto del proyecto si no fue provisto.
- [ ] Redactar `docs/requirements/PRD.md` con las 7 secciones.
- [ ] Logear en `.factory/log.jsonl`:
  `{"type": "step_complete", "step": "prd", "output_files": ["docs/requirements/PRD.md"]}`
- [ ] Confirmar al usuario que el PRD fue guardado y mostrar su ruta.

## Paso: project_memory_setup

### Paso opcional (paralelo a epics) — memoria de proyecto en `docs/memory/`

Genera contexto de dominio estable — el que un auditor humano o un agente frío necesita para entender el proyecto sin releer toda la conversación. Distinto del log cronológico de decisiones (`factory log memory`, ver `content/construction.md`): esto es una foto fija del dominio, no una bitácora que crece.

**Idempotencia:** correr una sola vez. Si `docs/memory/MEMORY.md` ya existe, no lo pises — el usuario o una fase posterior puede haberlo editado a mano.

## Pasos

- [ ] Si `docs/memory/MEMORY.md` ya existe: saltar este paso entero, no continuar.
- [ ] A partir del PRD, generar `docs/memory/*.md` (uno por tema, frontmatter `name`/`description`) para los temas que apliquen al proyecto:
  - `design_source.md` — ¿el proyecto tiene UI propia? ¿hay fuente de diseño (prototipo/export)? Si no aplica, decirlo explícitamente (N/A no es un hueco).
  - `deterministic_layer.md` — si el proyecto integra un LLM/IA en runtime: qué lógica NO puede delegarse a él (persistencia, validación de argumentos, invariantes de negocio).
  - `external_service_layer.md` — servicios externos/APIs de terceros que el proyecto integra.
  - `high_stakes_decisions.md` — decisiones de alto impacto que requieren explicabilidad hacia el usuario final (ej. escalar a humano, rechazar una operación).
  - `sensitive_data.md` — categorías de datos sensibles/PII que el proyecto maneja.
  - `server_side_secrets.md` — secretos que jamás deben llegar al cliente (tabla: secreto, dónde se usa, riesgo si se filtra).
- [ ] Omitir cualquier archivo cuyo tema no aplique al proyecto (ej. sin integraciones externas → no crear `external_service_layer.md`).
- [ ] Generar `docs/memory/MEMORY.md` como índice: una línea por archivo con su propósito.
- [ ] Logear `{"type": "step_complete", "step": "project_memory_setup", "output_files": [...lista de archivos creados...]}`.

## Paso: epics

### Paso 2: epics — EPIC-N.md

Produce `docs/requirements/epics/EPIC-N.md` - un archivo por cada epica.
Requiere que `docs/requirements/PRD.md` exista.

## Verificacion de prerequisitos

- Si `docs/requirements/PRD.md` no existe: mostrar error y sugerir correr el paso `prd` primero. No continuar.

## Reglas de redaccion

- Una sola pasada para todas las epicas - el agente necesita ver el conjunto completo para distribuir el alcance del PRD sin solapes entre epicas.
- Un archivo por epica: `docs/requirements/epics/EPIC-N.md` (N secuencial desde 1, nunca reutilizado).
- Frontmatter obligatorio: `id` (EPIC-N), `estado: draft`, `objetivo_prd` (a que objetivo del PRD responde esta epica).
- Cuerpo: meta de negocio de la epica + lista de HU por id (se completara en el paso `hu_por_epica` - por ahora la lista puede quedar vacia o con ids estimados).

## Sugerencia de capacidades transversales (OBLIGATORIO antes de cerrar)

Antes de logear step_complete, revisar si las siguientes capacidades estan cubiertas por alguna epica.
Sugerir al usuario (via pregunta explicita) las que falten - NUNCA agregarlas en silencio:

- Autenticacion / Login
- Gestion de perfil de usuario
- Cambio de contrasena
- Foto de perfil
- Recuperacion de cuenta
- Cualquier otra que la naturaleza del proyecto sugiera

Logear SIEMPRE este evento (aunque el usuario rechace todas las sugerencias):
`{"type": "advisor_note", "category": "sugerencia_transversal", "step": "epics", "suggestions": [...lista sugerida...], "accepted": [...lista aceptada...]}`

Crear epicas adicionales solo para las sugerencias que el usuario acepte explicitamente.

## Pasos

- [ ] Verificar que `docs/requirements/PRD.md` existe.
- [ ] Leer el PRD completo.
- [ ] Redactar todas las epicas en una sola pasada; crear un archivo por epica en `docs/requirements/epics/`.
- [ ] Revisar capacidades transversales y preguntar al usuario por las que falten.
- [ ] Logear el evento `advisor_note` de sugerencia_transversal.
- [ ] Crear epicas adicionales solo para las sugerencias aceptadas.
- [ ] Logear `{"type": "step_complete", "step": "epics", "output_files": [...lista de archivos creados...]}`.

## Paso: hu_por_epica

### Paso 3: hu_por_epica — HU-N.M.md (una instancia por epica)

Produce `docs/requirements/stories/HU-N.M.md` para todas las HU de UNA epica.
Se invoca una vez por epica. Si el proveedor soporta subagentes paralelos, cada instancia corre en paralelo para su epica; si no, se corre una a la vez de forma secuencial - NUNCA en una sola pasada para todas las epicas juntas.

## Prerequisitos

- `docs/requirements/PRD.md` debe existir.
- `docs/requirements/epics/EPIC-N.md` (la epica asignada a esta instancia) debe existir.
- Si alguno falta: mostrar error, listar que falta, sugerir el paso previo. No continuar.

## Contexto de esta instancia

Esta instancia recibe SOLO:
- El PRD completo.
- Su `EPIC-N.md` completa.
- El listado de ids de las demas epicas (NUNCA su contenido completo - para mantener el contexto acotado).

## Reglas de redaccion

- Un archivo por HU: `docs/requirements/stories/HU-N.M.md`.
- ID: `HU-N.M` donde N = numero de la epica duena, M = secuencial dentro de esa epica desde 1.
- IDs asignados una vez, nunca reutilizados. Si una HU se retira: cambiar frontmatter `estado: retirada` y mover a `stories/retiradas/`.
- Frontmatter obligatorio: `id`, `epica`, `estado: draft`, `prioridad` (alta/media/baja), `depende_de` (lista de ids, puede ser vacia).
- `depende_de` puede referenciar HU de esta epica o de otras - usar solo el id, NUNCA el contenido de la otra epica.
- Cuerpo: formato *Como [rol] quiero [accion] para [beneficio]* + al menos un criterio Given/When/Then.
- Tantos criterios Given/When/Then como casos relevantes (felices y de borde a nivel de negocio).
- **Anexo funcional** (solo si la HU toca una pantalla o un endpoint): que campos, que validaciones de negocio, que estados visibles, que datos entran/salen - en terminos de negocio, sin tecnicismos (sin nombres de tablas, verbos HTTP, componentes de UI concretos).

## Pasos

- [ ] Leer el PRD completo y `EPIC-N.md`.
- [ ] Redactar todas las HU de esta epica en una sola pasada (todos los archivos a la vez).
- [ ] Actualizar `EPIC-N.md` con la lista definitiva de ids de HU generadas.
- [ ] Logear `{"type": "step_complete", "step": "hu_por_epica", "epic": "EPIC-N", "output_files": [...lista de archivos creados...]}`.

## Paso: traceability

### Paso 4: traceability — traceability.md

Produce `docs/requirements/traceability.md` - tabla con una fila por cada HU no retirada.
Requiere que todos los pasos `hu_por_epica` esten completos en el log.
Corre en paralelo con el paso `flujos` (ambos dependen solo de `hu_por_epica`).

## Prerequisitos

- Todos los archivos `docs/requirements/stories/HU-N.M.md` generados (todos los eventos `step_complete` de `hu_por_epica` presentes en el log).
- Si alguna epica no tiene su paso completo en el log: listar cuales faltan y no continuar.

## Output

Archivo `docs/requirements/traceability.md` con tabla markdown:

```
| HU | Epica | Estado | Casos de prueba | Componentes de arquitectura |
|----|-------|--------|------------------|------------------------------|
| HU-1.1 | EPIC-1 | draft | _pendiente (fase QA)_ | _pendiente (fase Arquitectura)_ |
```

- Una fila por cada HU no retirada (excluir las de `stories/retiradas/`).
- Columnas "Casos de prueba" y "Componentes de arquitectura" quedan como `_pendiente (fase X)_` - se completan en fases futuras.

## Pasos

- [ ] Leer todos los archivos `docs/requirements/stories/HU-N.M.md` (excluyendo `retiradas/`).
- [ ] Generar `docs/requirements/traceability.md` con una fila por HU, en orden de id.
- [ ] Logear `{"type": "step_complete", "step": "traceability", "output_files": ["docs/requirements/traceability.md"]}`.

## Paso: flujos

### Paso 5: flujos — FLUJO-N.md

Produce `docs/requirements/flujos/FLUJO-N.md` - un archivo por cada flujo de negocio identificado.
Corre en paralelo con el paso `traceability` (ambos dependen solo de `hu_por_epica`).

## Prerequisitos

- Todos los archivos `docs/requirements/stories/HU-N.M.md` disponibles.
- NO requiere `traceability.md` (son pasos independientes).

## Que es un flujo de negocio

- Flujos de NEGOCIO, no de navegacion de UI (Arquitectura no existe todavia).
- Se derivan de las relaciones `depende_de` entre HU y de la narrativa de las Epicas.
- Solo crear flujos que representen un camino real que un usuario recorreria para lograr un objetivo de negocio (alta de cuenta, compra, publicacion de contenido, etc.).
- No todo par de HU relacionadas forma un flujo relevante.
- Arquitectura, cuando defina la navegacion real en `SCREEN-N.md`, tiene que honrar estos flujos ya declarados.

## Formato de cada archivo

- ID: `FLUJO-N`, secuencial desde 1, nunca reutilizado.
- Frontmatter: `id`, `estado: draft`, `hu` (lista ORDENADA de ids `HU-x.y` que el flujo recorre - puede cruzar varias Epicas).
- Cuerpo:
  - Nombre del flujo (ej. "Alta de cuenta y primer login").
  - Descripcion paso a paso de que hace el usuario en cada HU de la secuencia.
  - **Criterio de exito del flujo completo** - distinto de los criterios de aceptacion de cada HU aislada. Un flujo puede fallar aunque cada HU pase sus propios tests (ej. el dato que HU-1.3 guarda no es el que HU-2.1 espera leer).

## Pasos

- [ ] Leer todas las HU de todas las epicas en una sola pasada.
- [ ] Identificar secuencias de negocio coherentes que crucen multiples HU y representen objetivos reales.
- [ ] Crear un archivo `FLUJO-N.md` por cada flujo en `docs/requirements/flujos/`.
- [ ] Logear `{"type": "step_complete", "step": "flujos", "output_files": [...lista de archivos creados...]}`.

## Paso: audit_loop

### Paso 6: audit_loop — validacion, correccion y aprobacion humana

Loop auditor-constructor (maximo 3 iteraciones) + gate de aprobacion humana explicita.
No avanza a Arquitectura sin aprobacion del usuario.

## Prerequisitos

- `docs/requirements/traceability.md` debe existir (evento `step_complete` de `traceability` en el log).
- Al menos un `docs/requirements/flujos/FLUJO-N.md` (evento `step_complete` de `flujos` en el log).
- Si alguno falta: listar que falta y no continuar.

## Loop (maximo 3 iteraciones)

Por cada iteracion:

- [ ] **Checks deterministicos (1-7):** Correr `factory validate requirements --project-root . --log .factory/log.jsonl` y capturar la lista de errores.
- [ ] Si hay errores: corregirlos editando los archivos afectados, luego volver a correr el validator para confirmar que quedo limpio.
- [ ] **Checks semanticos (8-11):** Revisar con lectura propia del agente:
  - Check 8: Cada Epica tiene meta de negocio trazable a un objetivo explicito del PRD (sin epicas flotantes fuera del alcance declarado).
  - Check 9: No hay contradicciones entre criterios de aceptacion de HU distintas dentro de la misma epica.
  - Check 10: El alcance del PRD no tiene huecos evidentes en las epicas (cobertura), ni las epicas se salen del alcance (scope creep).
  - Check 11: Todo objetivo multi-paso del PRD tiene al menos un FLUJO-N que lo cubre de inicio a fin. Un flujo importante sin documentar es hallazgo BLOQUEANTE.
- [ ] Si hay hallazgos semanticos: corregirlos.
- [ ] Si ambas validaciones pasan: salir del loop antes de las 3 iteraciones.

## Gate de aprobacion humana (BLOQUEO DURO)

Despues del loop (con o sin iteraciones pendientes):

- [ ] Presentar resumen al usuario: numero de iteraciones realizadas, hallazgos encontrados y corregidos, hallazgos que quedaron pendientes (si los hay).
- [ ] Preguntar explicitamente al usuario (via el mecanismo de pregunta del proveedor detectado):
  **"Apruebas el conjunto completo de Requerimientos (PRD + Epicas + HU + Flujos + Trazabilidad) y autorizas avanzar a la fase de Arquitectura?"**
- [ ] Si el usuario dice NO: listar los puntos que senala, corregirlos, y volver a preguntar (no cuenta como iteracion del loop auditor).
- [ ] Si el usuario dice SI:
  - Logear `{"type": "step_complete", "step": "audit_loop", "iterations": N, "approved_by": "user"}`.
  - Marcar la fase de Requerimientos como completa.
- [ ] NUNCA avanzar a Arquitectura sin que `approved_by: "user"` este en el log - ni si el usuario lo pide de forma ambigua, ni "por cortesia".

## Manejo de errores

- Si cualquier paso falla con hallazgos no corregibles en <= 3 iteraciones: pausar, presentar al usuario los hallazgos pendientes, y esperar instrucciones antes de continuar.
- Si el usuario pide avanzar a Arquitectura sin que el log contenga `{"step": "audit_loop", "approved_by": "user"}`: negarse, explicar que falta la aprobacion del gate, listar que hallazgos quedaron pendientes.
