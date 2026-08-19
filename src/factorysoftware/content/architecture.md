---
id: architecture
steps:
  - id: adrs
    depende_de: ['constraints']
  - id: adrs_audit
    depende_de: ['adrs']
  - id: apis
    depende_de: ['data_model']
  - id: constraints
    depende_de: []
  - id: data_model
    depende_de: ['overview']
  - id: gap_check_and_traceability
    depende_de: ['apis', 'screens', 'ui_prototype']
  - id: integral_audit
    depende_de: ['gap_check_and_traceability']
  - id: overview
    depende_de: ['adrs_audit']
  - id: screens
    depende_de: ['apis']
  - id: ui_prototype
    depende_de: ['screens']
---

Content pack de la fábrica para la fase de architecture.

## Paso: adrs

Crea `docs/architecture/adrs/ADR-N.md`. Obligatorio definir Stack Tecnológico y Método de despliegue.

## Frontmatter
`id`, `estado`, `restricciones_aplicadas`, `nfr_aplicados`.

## Estructura
Contexto, Restricciones, Alternativas, Decisión, Recomendación, Consecuencias.

## Paso: adrs_audit

Checkpoint temprano. Verifica fundamentos teóricos reales, no violación de restricciones, existencia de NFRs en ADRs.

## Paso: apis

Genera `API-N.md`. Instancia por cada HU con anexo de endpoint.

## Paso: constraints

Crea `docs/architecture/constraints.md`.

## Verificaciones
- Preguntar restricciones duras, blandas y escenarios NFR.

## Salida
Archivo Markdown con 3 secciones y tabla de NFRs.

## Paso: data_model

Crea `docs/architecture/data-model.md` con Mermaid ER.

## Paso: gap_check_and_traceability

Verifica completitud estructural (1-6) y semántica (7-11). Actualiza `traceability.md`.

## Paso: integral_audit

Valida que PRD esté cubierto y no haya scope creep (i-iv).

## Paso: overview

Crea `docs/architecture/architecture-overview.md` con Mermaid C4.

## Paso: screens

Genera `SCREEN-N.md`. Instancia por cada HU con anexo de pantalla.

## Paso: ui_prototype

Crea código real corrible en rama `architecture/ui-prototype` bajo directorio `prototype/`.

