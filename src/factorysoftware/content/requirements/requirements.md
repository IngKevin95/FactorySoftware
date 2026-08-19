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
