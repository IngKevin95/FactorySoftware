# Skill de Arquitectura y Diseño — Diseño

Estado: aprobado
Subsistema: 3 de N (fase de contenido: Arquitectura) — depende del núcleo y
de Requerimientos, ver:
- `docs/superpowers/specs/2026-08-19-factory-core-design.md`
- `docs/superpowers/specs/2026-08-19-requirements-skill-design.md`

## Propósito

Content pack que toma el conjunto de Requerimientos (PRD, Épicas, HU,
traceability.md) y produce el diseño técnico completo del sistema: decisión
de stack y decisiones técnicas relevantes (ADRs), arquitectura general con
diagramas, modelo de datos, contratos de API y especificación de pantallas.
Este es el "cómo" que corresponde al "qué" ya congelado en Requerimientos —
ninguna decisión de negocio se toma ni se cambia acá; si una HU resulta
inviable con el stack elegido, se marca como hallazgo bloqueante y se
escala, no se reinterpreta la HU en silencio.

## No-objetivos

- Redefinir alcance de negocio (PRD/Épicas/HU) — son inputs de solo lectura
  para esta fase.
- Construcción real de código — es la fase de Construcción (spec futuro),
  que toma estos artefactos como su propio "norte" técnico.
- Casos de prueba — la fase de QA (spec futuro) toma API-N.md/SCREEN-N.md
  como contrato a validar.

## Conjunto de documentos y ubicación

```
docs/architecture/
  adrs/
    ADR-1.md
    ADR-2.md
    ...
  architecture-overview.md
  data-model.md
  apis/
    API-1.md
    API-2.md
    ...
  screens/
    SCREEN-1.md
    SCREEN-2.md
    ...
```

Mismo criterio que Requerimientos: un archivo por unidad, no documentos
monolíticos — diffs legibles y fan-out paralelizable por API/pantalla.

### Esquema de IDs y trazabilidad

- `ADR-N`, `API-N`, `SCREEN-N`: secuenciales, nunca reusados (mismo criterio
  de retiro que en Requerimientos: se marcan `estado: retirada`, no se
  borran).
- Cada `API-N.md` y `SCREEN-N.md` lleva frontmatter `implementa: [HU-x.y, ...]`
  — relación muchos-a-muchos (una HU puede necesitar más de un endpoint o
  pantalla; un endpoint puede servir a más de una HU).
- Al cerrar la fase, se actualiza la columna "Componentes de arquitectura" de
  `docs/requirements/traceability.md` con los ids de API/SCREEN que
  implementan cada HU — cierra el gap que quedó pendiente en el spec de
  Requerimientos.

## Formato de diagramas: Mermaid embebido

Todo diagrama (C4 context/container, secuencia, ER, flujos de estado) va
como bloque ` ```mermaid ` dentro del `.md` correspondiente — texto plano,
sin herramienta externa, se renderiza nativo en GitHub/GitLab/VS
Code/Artifacts. Ningún adapter de proveedor necesita nada especial para
producirlo, es contenido markdown normal.

## Contenido de cada documento

### `adrs/ADR-N.md`

Frontmatter: `id`, `estado` (propuesta/aceptada/retirada), `afecta_a`
(opcional, ids de otras ADR relacionadas). Cuerpo, formato ADR estándar:
contexto, decisión, alternativas consideradas con pros/contras de cada una,
**recomendación honesta del asesor** (puede diferir de lo que el usuario
pidió inicialmente — se documenta el desacuerdo igual que en el núcleo),
consecuencias. La primera ADR de toda fase es siempre la elección de stack
tecnológico, porque todo lo demás depende de ella.

### `architecture-overview.md`

Diagrama C4 nivel contexto (sistema y actores externos) y nivel contenedor
(servicios/apps/DBs y cómo se comunican), en Mermaid. Texto de acompañamiento
explicando decisiones de comunicación entre componentes (síncrono/asíncrono,
protocolos).

### `data-model.md`

Diagrama ER en Mermaid + descripción de entidades, atributos clave,
relaciones y restricciones relevantes de negocio (no DDL completo — el nivel
de detalle que necesita Construcción para generar el schema real).

### `apis/API-N.md`

Frontmatter: `id`, `implementa` (ids de HU), `estado`. Cuerpo: contrato
técnico completo del endpoint — método, ruta, request/response (schema y
ejemplo), códigos de error, autenticación/autorización aplicable. Nivel
OpenAPI-lite en prosa/tablas markdown (no se exige generar YAML OpenAPI
formal en v1 — evaluar como mejora futura si se necesita generar SDKs).

### `screens/SCREEN-N.md`

Frontmatter: `id`, `implementa` (ids de HU), `estado`, `apis_consumidas`
(ids de API-N que esta pantalla usa). Cuerpo: descripción de la pantalla a
nivel de wireframe textual (componentes, layout, estados — vacío/carga/error/
éxito), reglas de UI/UX (validaciones visibles, navegación, responsive
si aplica). No es diseño visual pixel-perfect (eso es una skill de UI
distinta, fuera de alcance); es el contrato funcional-técnico que
Construcción necesita para armar el componente real.

## Pipeline de ejecución (usa el mecanismo transversal del núcleo)

```
- id: adrs
  depende_de: []
  fan_out: null
  paralelizable: false
  # una sola pasada: la elección de stack y las decisiones técnicas
  # derivadas deben ser mutuamente coherentes, no se pueden decidir
  # en aislamiento

- id: overview
  depende_de: [adrs]
  fan_out: null
  paralelizable: false

- id: data_model
  depende_de: [overview]
  fan_out: null
  paralelizable: false

- id: apis
  depende_de: [data_model]
  fan_out: "una instancia por cada HU con anexo funcional de endpoint en Requerimientos"
  paralelizable: true
  # cada instancia recibe: la(s) HU relevante(s), data-model.md,
  # architecture-overview.md — no el contenido completo de las demás APIs

- id: screens
  depende_de: [apis]
  fan_out: "una instancia por cada HU con anexo funcional de pantalla en Requerimientos"
  paralelizable: true
  # depende de apis (no solo de data_model) porque cada pantalla necesita
  # conocer el contrato real de los endpoints que va a consumir

- id: gap_check_and_traceability
  depende_de: [apis, screens]
  fan_out: null
  paralelizable: false
  # actualiza traceability.md de Requerimientos con los ids de
  # API-N/SCREEN-N que implementan cada HU

- id: audit_loop
  depende_de: [gap_check_and_traceability]
  fan_out: null
  paralelizable: false
  # loop auditor-constructor del núcleo, hasta 3 iteraciones, después gate
  # de aprobación humana explícita
```

Si el proveedor no soporta despacho paralelo, `apis` y `screens` corren
instancia por instancia en serie, cada una logueada individualmente — mismo
criterio que en Requerimientos, nunca colapsan en una sola pasada gigante.

## Gate de aprobación

Bloqueo duro, igual que Requerimientos: no se avanza a Construcción sin
aprobación explícita del usuario sobre ADRs + overview + data model + APIs +
pantallas, después de que el loop de auditoría (núcleo, hasta 3 iteraciones)
cierre limpio.

## Checklist del auditor

Verificaciones estructurales (mecánicas):

1. Toda HU con anexo funcional de endpoint (Requerimientos) tiene al menos
   un `API-N.md` con `implementa` que la referencia — sin excepciones
   silenciosas.
2. Toda HU con anexo funcional de pantalla tiene al menos un `SCREEN-N.md`
   correspondiente.
3. Todo id en `apis_consumidas` de un `SCREEN-N.md` existe como `API-N.md`
   real.
4. Ningún `API-N.md`/`SCREEN-N.md` referencia en `implementa` una HU que no
   existe (o que está `retirada`).
5. `traceability.md` de Requerimientos queda con la columna "Componentes de
   arquitectura" completa para toda HU no retirada.

Verificaciones de juicio (semánticas):

6. El stack elegido (ADR-1) es técnicamente capaz de cumplir los criterios
   de aceptación de las HU que dependen de él (ej. si una HU exige tiempo
   real y el stack elegido no soporta bien ese patrón, es un hallazgo
   bloqueante, no un detalle menor).
7. Los diagramas de `architecture-overview.md` son coherentes con lo que
   describen `data-model.md` y los `API-N.md` (sin componentes en el
   diagrama que no tienen contrato, ni contratos de componentes ausentes del
   diagrama).
8. Las ADR no se contradicen entre sí (ninguna decisión posterior invalida
   silenciosamente una anterior sin una nueva ADR que la reemplace
   explícitamente marcando la vieja como `retirada`).

Las verificaciones 1–5 se ejecutan de forma determinística; las 6–8 quedan a
cargo del paso de auditoría semántica definido en el núcleo.

## Extensión del CLI del núcleo

`factory validate architecture` — corre las verificaciones estructurales
1–5 sobre `docs/architecture/` cruzado con `docs/requirements/`, devuelve
lista de problemas (vacía si todo bien). Mismo patrón que
`factory validate requirements`.

## Manejo de errores / casos borde

- Una HU con anexo funcional de endpoint que el stack elegido no puede
  cumplir tal como está redactada: hallazgo bloqueante de la verificación 6,
  se escala al usuario con la ADR y la HU en conflicto — no se reinterpreta
  la HU para que "encaje" sin decírselo al usuario.
- `SCREEN-N.md` que consume un `API-N.md` todavía no generado (por orden de
  ejecución roto): la validación estructural 3 lo detecta antes de llegar al
  gate humano.
- ADR que reemplaza una decisión anterior sin marcar la vieja como retirada:
  hallazgo bloqueante de la verificación 8, no queda como ambigüedad
  silenciosa en el historial de decisiones.

## Testing

pytest, cero IO externo, fixtures de árbol de documentos en `tmp_path`:

- `test_validate_architecture.py`: caso positivo completo y un caso negativo
  por cada verificación estructural 1–5 (HU de endpoint sin API, HU de
  pantalla sin screen, `apis_consumidas` inexistente, `implementa` con HU
  inexistente/retirada, columna de trazabilidad incompleta).

## Preguntas abiertas para specs futuros

- El chequeo de "gaps entre fases" para Construcción (¿todo API-N/SCREEN-N
  tiene código real que lo implemente?) queda para el spec de Construcción,
  que debe definir su propio `factory validate construction` sobre el mismo
  patrón.
