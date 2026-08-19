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
  constraints.md
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

El único artefacto de esta fase que no es markdown puro es el prototipo de
UI, que vive fuera de `docs/`, en `prototype/` sobre la rama
`architecture/ui-prototype` — ver sección "Prototipo de UI" más abajo.

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

## Ninguna decisión sin validar y contrastar contra teoría

Esta fase es donde más pesa el rol de asesor/auditor definido en el núcleo:
**el agente no tiene permitido tomar ninguna decisión técnica (stack,
artefactos y método de despliegue, patrón de comunicación, elección de base
de datos, etc.) sin antes contrastarla explícitamente contra teoría/práctica
establecida y contra las restricciones del proyecto.** No alcanza con
documentar pros/contras de memoria — cada alternativa considerada necesita
una justificación de por qué la teoría/práctica de la industria la favorece
o la desaconseja para este caso puntual, no una opinión genérica.

### `constraints.md`

Documento único (lista corta, no amerita un archivo por ítem), completado al
inicio de la fase, antes de cualquier ADR:

- **Restricciones duras**: no negociables — cumplimiento normativo,
  infraestructura ya existente que hay que respetar, presupuesto,
  tecnologías mandatadas explícitamente por el usuario. Ninguna ADR puede
  proponer algo que las viole; si el agente detecta que una restricción dura
  es técnicamente inviable en conjunto con otra, es un hallazgo bloqueante
  que se escala, no se resuelve solo.
- **Restricciones blandas**: preferencias — se pueden pisar en una ADR
  siempre que la justificación teórica sea explícita y quede registrada por
  qué se decidió no seguirlas.
- **Escenarios de calidad (NFR medibles)**: requisitos no funcionales
  expresados como escenario verificable, no como adjetivo ("rápido",
  "escalable" no son escenarios). Formato tabla, estilo ATAM:

  | ID | Estímulo | Entorno | Respuesta | Medida de respuesta |
  |----|----------|---------|-----------|----------------------|
  | NFR-1 | 500 usuarios concurrentes hacen checkout | Producción, hora pico | Sistema procesa sin degradar | p95 de latencia < 200ms |

  Se completan a partir de HU/PRD que ya insinúan un NFR (ej. una HU que
  menciona "en tiempo real" o "muchos usuarios a la vez") más lo que el
  Asesor eliza y sugiere explícitamente si detecta un NFR implícito que
  nadie escribió — mismo patrón de sugerencia-no-silenciosa que las
  pantallas transversales de Requerimientos. Un proyecto sin NFR relevantes
  puede dejar la tabla vacía; lo que no puede pasar es que exista un NFR
  real (mencionado en alguna HU) y no quede acá como escenario medible.

Toda ADR referencia qué restricciones y qué escenarios de calidad de
`constraints.md` aplicó.

### `adrs/ADR-N.md`

Frontmatter: `id`, `estado` (propuesta/aceptada/retirada), `afecta_a`
(opcional, ids de otras ADR relacionadas), `restricciones_aplicadas` (ids/
nombres de restricciones de `constraints.md`), `nfr_aplicados` (ids `NFR-N`
de la tabla de escenarios de calidad que esta decisión atiende, o `N/A` si
ninguno aplica — nunca se omite el campo, se declara explícitamente que no
aplica). Cuerpo, formato ADR extendido — cada sección es obligatoria, no se
puede omitir por "obvia":

1. **Contexto**: qué problema técnico se resuelve.
2. **Restricciones y escenarios de calidad aplicables**: cuáles de
   `constraints.md` entran en juego, incluyendo qué `NFR-N` atiende esta
   decisión si corresponde.
3. **Alternativas consideradas**: mínimo 2 opciones reales (nunca una sola
   opción "porque sí"). Por cada una: **fundamento teórico** — qué práctica,
   patrón, benchmark o consenso de la industria la respalda o la
   desaconseja para este contexto puntual (ej. "CQRS se recomienda cuando
   las cargas de lectura/escritura son muy asimétricas — acá HU-3.x indica
   ese patrón de uso, por eso se prefiere sobre CRUD simple"), no una
   afirmación sin sustento.
4. **Decisión**: cuál se elige.
5. **Recomendación honesta del asesor**: si la decisión del usuario difiere
   de lo que la teoría sugeriría para este contexto, se documenta el
   desacuerdo explícitamente (mismo mecanismo del núcleo: `advisor_note` o
   `advisor_block` según la categoría de riesgo).
6. **Consecuencias**: qué se gana, qué se sacrifica, qué queda más difícil
   de cambiar después.

Las ADR fundacionales, obligatorias en toda fase antes de que cualquier otro
paso del pipeline pueda avanzar, son como mínimo:
- **Stack tecnológico** — porque todo lo demás depende de ella.
- **Artefactos y método de despliegue** (ej. imagen de contenedor vs binario
  vs paquete serverless; pipeline de CI/CD; entorno destino) — porque
  `architecture-overview.md` necesita saber esto para el diagrama de
  contenedores, y no es un detalle que se pueda dejar implícito o para
  después.

Cualquier otra decisión técnica que surja de las HU (ej. elección de motor
de base de datos, patrón de mensajería) se documenta como ADR adicional
siguiendo el mismo formato de 6 secciones.

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
si aplica). No es diseño visual pixel-perfect; es el contrato
funcional-técnico que tanto el prototipo (`ui_prototype`, siguiente paso)
como Construcción usan para armar el componente real.

Las reglas de navegación de cada pantalla deben **honrar** los flujos de
negocio ya declarados en `docs/requirements/flujos/FLUJO-N.md` (Requerimientos
los define primero, sin saber todavía la navegación técnica real —
Arquitectura es quien la resuelve, pero sin contradecir la secuencia de
negocio ya aprobada). QA va a usar `flujos/FLUJO-N.md` directamente para
armar sus tests e2e, así que si la navegación real de las pantallas no
coincide con el flujo declarado, es un hallazgo que se detecta acá, no
recién cuando QA intente escribir un test que no puede recorrerse.

## Prototipo de UI: ubicación, rama y revisión asistida

A diferencia del resto de esta fase (solo documentación), `ui_prototype`
produce código real corrible. Vive en una rama dedicada
`architecture/ui-prototype`, creada desde `develop`, en una carpeta
`prototype/` en la raíz del repo — separada del código de producción que
Construcción arma después, para que quede claro que es un artefacto de
validación, no el componente final todavía.

Revisión: el usuario debe poder correrlo y verlo/interactuarlo antes de
aprobar la fase (usar el skill `run` del proyecto si está disponible, o las
instrucciones de arranque que el propio prototipo documenta). Esto es lo que
hace la construcción "asistida" — no es solo un documento que el usuario lee
y aprueba a ciegas, es algo que se prueba.

No es descartable: cuando Construcción arranca la rama `feature/EPIC-N-...`
de una épica, la crea desde `architecture/ui-prototype` (si existe y fue
aprobado) en vez de desde `develop` a secas, y las tareas de rol `frontend`
refinan ese código de prototipo a producción en vez de reescribirlo de cero.
Esto ajusta `branch_setup` en el spec de Construcción (ver ese spec).

## Pipeline de ejecución (usa el mecanismo transversal del núcleo)

Arquitectura, igual que Requerimientos, no declara unidad principal de
fan-out (sus fan-out son por HU/pantalla, no por una unidad organizadora
como la Épica) — expone 2 de los 4 tipos de skill del núcleo:

- `architecture-<step_id>` (ej. `architecture-apis`) — modo manual, con el
  chequeo de prerequisitos del núcleo: pedir `architecture-apis` sin que
  `adrs_audit` haya cerrado no ejecuta nada, informa qué falta y sugiere
  correrlo primero.
- `architecture-flujo` — modo completo, encadena todo desde `constraints`
  hasta `integral_audit` y el gate.

Sin `architecture-slide` ni `architecture-auditor`.

```
- id: constraints
  depende_de: []
  fan_out: null
  paralelizable: false
  # constraints.md se completa antes que cualquier ADR — toda decisión
  # posterior debe poder referenciarlo

- id: adrs
  depende_de: [constraints]
  fan_out: null
  paralelizable: false
  # una sola pasada: la elección de stack, el método de despliegue y las
  # decisiones técnicas derivadas deben ser mutuamente coherentes, no se
  # pueden decidir en aislamiento

- id: adrs_audit
  depende_de: [adrs]
  fan_out: null
  paralelizable: false
  # checkpoint temprano obligatorio, mismo mecanismo de loop del núcleo
  # (hasta 3 iteraciones) pero aplicado SOLO a las ADR, antes de dejar que
  # overview/data_model/apis/screens construyan sobre una decisión mala:
  # verifica que cada ADR tenga fundamento teórico real (no una opinión sin
  # sustento) y que ninguna restricción dura de constraints.md fue violada

- id: overview
  depende_de: [adrs_audit]
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

- id: ui_prototype
  depende_de: [screens]
  fan_out: "una instancia por cada SCREEN-N.md generado"
  paralelizable: true
  # convierte el wireframe textual de cada SCREEN-N.md en un prototipo real
  # corrible/clickeable (no descriptivo), usando el stack de la ADR de
  # arquitectura cuando aplica, o HTML/CSS plano si conviene ir más rápido.
  # No es descartable: Construcción lo toma como punto de partida y lo
  # refina a producción en vez de reconstruir desde cero (ver sección de
  # ubicación y rama más abajo)

- id: gap_check_and_traceability [rol: Auditor de fase]
  depende_de: [apis, screens, ui_prototype]
  fan_out: null
  paralelizable: false
  # Auditor (checklist estructural 1-6 + semántico 7-10, ver más abajo).
  # Actualiza traceability.md de Requerimientos con los ids de
  # API-N/SCREEN-N que implementan cada HU

- id: integral_audit [rol: Auditor Integral]
  depende_de: [gap_check_and_traceability]
  fan_out: null
  paralelizable: false
  # último paso agéntico antes del gate humano: lee Requerimientos +
  # Arquitectura completos y valida que ningún objetivo/métrica de éxito
  # del PRD quedó sin cobertura arquitectónica, y que ninguna ADR/API/
  # pantalla introdujo alcance sin respaldo en una HU real (scope creep) —
  # ver checklist propio más abajo
```

Si el proveedor no soporta despacho paralelo, `apis` y `screens` corren
instancia por instancia en serie, cada una logueada individualmente — mismo
criterio que en Requerimientos, nunca colapsan en una sola pasada gigante.

## Gate de aprobación

Bloqueo duro, igual que Requerimientos: no se avanza a Construcción sin
aprobación explícita del usuario sobre ADRs + overview + data model + APIs +
pantallas, después de que **ambos** roles de auditoría del núcleo cierren
limpio, en orden: primero el Auditor de fase (`gap_check_and_traceability`),
después el Auditor Integral (`integral_audit`) — cada uno con su propio tope
de 3 iteraciones.

## Checklist del auditor

### Checklist de `adrs_audit` (checkpoint temprano, antes de `overview`)

Todas de juicio (no hay atajo mecánico para evaluar si un fundamento teórico
es real):

a. Cada ADR tiene al menos 2 alternativas reales consideradas, cada una con
   fundamento teórico explícito (práctica, patrón, benchmark o consenso de
   industria citado) — una alternativa sin fundamento, o un fundamento
   genérico tipo "es más rápido" sin contexto, es hallazgo bloqueante.
b. Ninguna decisión viola una restricción dura de `constraints.md`. Si una
   ADR pisa una restricción blanda, la justificación teórica de por qué
   está explícita.
c. Existen como mínimo las ADR fundacionales obligatorias: stack tecnológico
   y artefactos/método de despliegue.
d. Si la decisión final difiere de lo que el fundamento teórico sugeriría
   como mejor opción para el contexto, la sección "Recomendación honesta del
   asesor" documenta ese desacuerdo — no puede quedar una ADR donde el
   agente decidió en contra de la teoría sin decirlo.
e. Todo `NFR-N` de la tabla de escenarios de calidad en `constraints.md`
   queda atendido por al menos una ADR con ese id en `nfr_aplicados` — un
   NFR medible sin ninguna decisión que lo atienda es hallazgo bloqueante,
   no queda como "implícito" en el stack elegido. A diferencia de a–d, esta
   es una verificación de referencia cruzada, no de juicio — se puede (y
   debe) correr también de forma mecánica vía `factory validate architecture`.

### Checklist del cierre de fase (después de `screens`, antes del gate)

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
6. Todo `SCREEN-N.md` tiene su contraparte corrible en `prototype/` sobre la
   rama `architecture/ui-prototype` — un `SCREEN-N.md` sin prototipo real es
   hallazgo bloqueante, no queda como "pendiente para después".

Verificaciones de juicio (semánticas):

7. El stack elegido (ADR-1) es técnicamente capaz de cumplir los criterios
   de aceptación de las HU que dependen de él (ej. si una HU exige tiempo
   real y el stack elegido no soporta bien ese patrón, es un hallazgo
   bloqueante, no un detalle menor).
8. Los diagramas de `architecture-overview.md` son coherentes con lo que
   describen `data-model.md` y los `API-N.md` (sin componentes en el
   diagrama que no tienen contrato, ni contratos de componentes ausentes del
   diagrama).
9. El prototipo corrible de cada pantalla refleja fielmente los estados y
   reglas de UI/UX descritos en su `SCREEN-N.md` (vacío/carga/error/éxito,
   validaciones visibles) — no es solo "algo que corre", tiene que cumplir
   el contrato.
10. Las ADR no se contradicen entre sí (ninguna decisión posterior invalida
    silenciosamente una anterior sin una nueva ADR que la reemplace
    explícitamente marcando la vieja como `retirada`).
11. Todo `FLUJO-N.md` de Requerimientos es recorrible con la navegación real
    declarada en las pantallas involucradas — cada paso del flujo tiene una
    pantalla/API que lo resuelve, en el orden correcto.

Las verificaciones 1–6 se ejecutan de forma determinística; las 7–11 y a–d
quedan a cargo del paso de auditoría semántica definido en el núcleo.

### Checklist de `integral_audit` (rol: Auditor Integral)

Todas de juicio, sobre Requerimientos + Arquitectura leídos como un
conjunto, no solo cruzando ids:

i. Todo objetivo y métrica de éxito del `PRD.md` tiene al menos una
   decisión de arquitectura (ADR, componente del overview, o API/pantalla)
   que contribuye a cumplirlo — un objetivo del PRD sin ningún respaldo
   arquitectónico es un hallazgo bloqueante, no una omisión menor.
ii. Ninguna ADR, componente de `architecture-overview.md`, `API-N.md` o
   `SCREEN-N.md` introduce capacidad/alcance que no está pedido ni
   implícito en ninguna HU o en el PRD (scope creep técnico — ej. una ADR
   que agrega un módulo de analytics que ninguna HU pidió).
iii. El alcance explícitamente excluido en el PRD ("qué explícitamente no
   entra") no aparece resuelto ni parcialmente construido en ningún
   artefacto de Arquitectura.
iv. Las restricciones duras de `constraints.md` siguen siendo consistentes
   con las restricciones/supuestos declarados en el PRD (si el PRD asume
   algo que `constraints.md` contradice, es un hallazgo bloqueante, no una
   ADR que lo resuelve en silencio).

Este checklist es deliberadamente distinto del de `gap_check_and_traceability`:
ese verifica que los documentos *se referencien* correctamente entre sí; este
verifica que el *contenido* de una fase siga siendo fiel a la intención de la
fase anterior.

## Extensión del CLI del núcleo

`factory validate architecture` — corre las verificaciones estructurales
1–6 sobre `docs/architecture/` (incluyendo que exista el prototipo corrible
de cada `SCREEN-N.md`) cruzado con `docs/requirements/`, devuelve lista de
problemas (vacía si todo bien). Mismo patrón que `factory validate
requirements`.

## Manejo de errores / casos borde

- Una HU con anexo funcional de endpoint que el stack elegido no puede
  cumplir tal como está redactada: hallazgo bloqueante de la verificación 7,
  se escala al usuario con la ADR y la HU en conflicto — no se reinterpreta
  la HU para que "encaje" sin decírselo al usuario.
- `SCREEN-N.md` que consume un `API-N.md` todavía no generado (por orden de
  ejecución roto): la validación estructural 3 lo detecta antes de llegar al
  gate humano.
- `SCREEN-N.md` sin prototipo corrible correspondiente: hallazgo bloqueante
  de la verificación estructural 6, detectado antes del gate.
- ADR que reemplaza una decisión anterior sin marcar la vieja como retirada:
  hallazgo bloqueante de la verificación 10, no queda como ambigüedad
  silenciosa en el historial de decisiones.
- ADR con una sola alternativa "obvia" y sin fundamento teórico citado: el
  checkpoint `adrs_audit` la rechaza antes de que `overview` llegue a
  construir sobre ella — no se descubre recién al final de la fase.
- Restricción dura violada por una ADR: hallazgo bloqueante del checkpoint
  `adrs_audit` (verificación b), se escala antes de avanzar, nunca se
  documenta como "excepción aceptada" sin decisión explícita del usuario.

## Testing

pytest, cero IO externo, fixtures de árbol de documentos en `tmp_path`:

- `test_validate_architecture.py`: caso positivo completo y un caso negativo
  por cada verificación estructural 1–6 (HU de endpoint sin API, HU de
  pantalla sin screen, `apis_consumidas` inexistente, `implementa` con HU
  inexistente/retirada, columna de trazabilidad incompleta, SCREEN-N sin
  prototipo corrible), más un caso negativo para la verificación e de
  `adrs_audit` (NFR-N en `constraints.md` sin ninguna ADR que lo referencie
  en `nfr_aplicados`).

## Preguntas abiertas para specs futuros

- El chequeo de "gaps entre fases" para Construcción (¿todo API-N/SCREEN-N
  tiene código real que lo implemente?) queda para el spec de Construcción,
  que debe definir su propio `factory validate construction` sobre el mismo
  patrón.
