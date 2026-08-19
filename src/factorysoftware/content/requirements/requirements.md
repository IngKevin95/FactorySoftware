---
id: requirements
steps:
  - id: prd
    depende_de: []
    fan_out: null
    paralelizable: false
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
---

Content pack de la fábrica que guía al agente para producir el conjunto de documentos de Requerimientos de un proyecto: PRD, Épicas, Historias de Usuario (HU), Flujos de negocio y una matriz de trazabilidad. Este conjunto es el norte funcional de todo el proyecto — Construcción y QA se validan contra él, no al revés. Ningún detalle técnico (contratos de API, diseño de pantallas, arquitectura) se define acá; eso es responsabilidad de la fase de Arquitectura.

## Paso: prd

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

## Paso: epics

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
