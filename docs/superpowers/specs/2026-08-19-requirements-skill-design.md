# Skill de Ingeniería de Requerimientos — Diseño

Estado: aprobado
Subsistema: 2 de N (fase de contenido: Requerimientos) — depende del núcleo,
ver `docs/superpowers/specs/2026-08-19-factory-core-design.md`.

## Propósito

Content pack de la fábrica que guía al agente para producir el conjunto de
documentos de requerimientos de un proyecto: PRD, Épicas, Historias de
Usuario (HU) y una matriz de trazabilidad explícita. Este conjunto es el
**norte funcional** de todo el proyecto — construcción y QA se validan
contra él, no al revés. Ningún detalle técnico (contratos de API, diseño de
pantallas, arquitectura) se define acá; eso es responsabilidad de la fase de
Arquitectura, que toma este conjunto como input.

## No-objetivos

- Diseño técnico de API, pantallas o UI/UX — vive en la fase de Arquitectura
  (subsistema separado, spec futuro), informado por este contenido.
- Definir el mecanismo genérico de loop auditor-constructor ni el schema de
  log — ya están definidos en el núcleo y se reutilizan tal cual.
- Cobertura de QA real (casos de prueba) — la matriz de trazabilidad tiene
  una columna para casos de prueba, pero se llena cuando exista la fase de
  QA; acá queda vacía/pendiente.

## Conjunto de documentos y ubicación

```
docs/requirements/
  PRD.md
  epics/
    EPIC-1.md
    EPIC-2.md
    ...
  stories/
    HU-1.1.md
    HU-1.2.md
    HU-2.1.md
    ...
  traceability.md
```

Un archivo por Épica y por HU (no documentos monolíticos) — cada uno más
fácil de editar/revisar sin tocar el resto, y con diffs de git legibles por
unidad de negocio.

### Esquema de IDs

- `EPIC-N`: secuencial, asignado una vez, nunca reusado.
- `HU-N.M`: N = número de épica dueña, M = secuencial dentro de esa épica.
- Si una HU o Épica se retira, su archivo **no se borra ni se reusa el id**:
  se le cambia el frontmatter `estado: retirada` y se mueve a
  `stories/retiradas/` o `epics/retiradas/`. Esto preserva la integridad de
  la trazabilidad histórica (una HU referenciada por un commit o un test
  viejo sigue siendo encontrable).

## Pipeline de ejecución (usa el mecanismo transversal del núcleo)

Sigue el formato de declaración de pasos definido en el spec del núcleo, y
por lo tanto cada paso es invocable manualmente (ej. "generá solo el PRD",
"armá las HU de EPIC-2") con el chequeo de prerequisitos del núcleo — pedir
`hu_por_epica` sin que `epics` esté completo no ejecuta nada, informa qué
falta y sugiere correrlo primero — además del modo automático que encadena
todo hasta `audit_loop`. La
generación de HU por épica es el único paso con fan-out paralelizable: cada
épica ya tiene su meta de negocio fijada por el paso anterior, así que
redactar las HU de una épica no requiere ver las HU de las demás — candidato
correcto para despacho paralelo. Épicas, en cambio, necesitan verse entre sí
para no solaparse en alcance, por eso corre como paso único (no fan-out).

```
- id: prd
  depende_de: []
  fan_out: null
  paralelizable: false

- id: epics
  depende_de: [prd]
  fan_out: null
  paralelizable: false
  # una sola pasada que redacta TODAS las épicas juntas, así el agente
  # puede repartir el alcance del PRD entre ellas sin solapes. Antes de
  # cerrar el paso, el Asesor revisa el set de épicas resultante y sugiere
  # explícitamente capacidades transversales típicas de una aplicación
  # completa que no estén cubiertas (autenticación/login, gestión de
  # perfil, cambio de contraseña, foto de perfil, recuperación de cuenta,
  # y cualquier otra que la naturaleza del proyecto sugiera) — nunca las
  # agrega en silencio. Cada sugerencia se presenta al usuario (vía
  # AskUserQuestion o equivalente del proveedor) y solo se crea una Épica/HU
  # nueva para las que el usuario confirma explícitamente.

- id: hu_por_epica
  depende_de: [epics]
  fan_out: "una instancia por cada EPIC-N creada en el paso anterior"
  paralelizable: true
  # cada instancia solo recibe: el PRD, su propia EPIC-N.md, y el listado
  # de ids de las demás épicas (para depende_de entre HU de distinta
  # épica) — nunca el contenido completo de las otras épicas

- id: traceability
  depende_de: [hu_por_epica]
  fan_out: null
  paralelizable: false
  # agrega: una fila por cada HU generada en el paso anterior (necesita
  # ver el resultado completo de todas las instancias de fan-out)

- id: audit_loop
  depende_de: [traceability]
  fan_out: null
  paralelizable: false
  # loop auditor-constructor del núcleo, hasta 3 iteraciones, después gate
  # de aprobación humana explícita
```

Si el proveedor no soporta despacho paralelo de subagentes, `hu_por_epica`
igual corre como pasos separados por épica (uno a la vez, cada uno logueado
individualmente) — nunca colapsa en una sola pasada que redacte todas las HU
de todas las épicas juntas, porque eso reintroduce el problema de contexto
que el fan-out evita.

## Contenido de cada documento

### `PRD.md`

Problema a resolver, objetivo de negocio, alcance (qué entra / qué
explícitamente no entra), métricas de éxito, stakeholders, restricciones y
supuestos conocidos. Sin detalle técnico.

### `epics/EPIC-N.md`

Frontmatter: `id`, `estado` (draft/validada/retirada), `objetivo_prd` (a qué
objetivo del PRD responde). Cuerpo: meta de negocio de la épica, lista de HU
que contiene (referenciada por id, no duplicada).

### `stories/HU-N.M.md`

Frontmatter: `id`, `epica`, `estado` (draft/validada/bloqueada/retirada),
`prioridad`, `depende_de` (lista de ids de HU, opcional).

Cuerpo:
- Formato estándar: *Como [rol] quiero [acción] para [beneficio]*.
- Criterios de aceptación en Given/When/Then, al menos uno, tantos como
  hagan falta para cubrir los casos relevantes (felices y de borde a nivel
  de negocio).
- **Anexo funcional** (solo si la HU toca una pantalla o un endpoint): detalle
  a nivel de negocio — qué campos, qué validaciones de negocio, qué estados
  visibles tiene la pantalla, qué datos entran/salen del endpoint en
  términos de negocio. Sigue siendo el "qué", nunca el "cómo" (sin nombres
  de tablas, sin verbos HTTP, sin componentes de UI concretos — eso lo
  decide Arquitectura).

### `traceability.md`

Tabla markdown, una fila por HU:

| HU | Épica | Estado | Casos de prueba | Componentes de arquitectura |
|----|-------|--------|------------------|------------------------------|
| HU-1.1 | EPIC-1 | validada | _pendiente (fase QA)_ | _pendiente (fase Arquitectura)_ |

Documento vivo, mantenido a mano por quien cierra cada fase — no autogenerado
por una herramienta separada (evita construir infraestructura de consulta
antes de necesitarla). El loop auditor (ver más abajo) sí verifica
mecánicamente que no haya HU sin fila ni filas huérfanas.

## Gate de aprobación

Bloqueo duro: la skill no marca la fase de Requerimientos como completa ni
habilita avanzar a Arquitectura sin que el usuario apruebe explícitamente
PRD + Épicas + HU (vía `AskUserQuestion` en Claude Code, o el mecanismo
equivalente de pregunta al usuario del proveedor detectado). Sigue el
mecanismo transversal de loop auditor-constructor definido en el núcleo:
hasta 3 iteraciones de auditoría automática antes del gate humano.

## Checklist del auditor (usado en cada iteración del loop del núcleo)

Verificaciones estructurales (mecánicas, no requieren juicio):

1. Toda Épica referenciada en `traceability.md` tiene archivo en `epics/`.
2. Toda HU referenciada en algún `epics/EPIC-N.md` tiene archivo en
   `stories/` y viceversa (sin HU huérfanas en ningún sentido).
3. Todo id en `depende_de` de una HU existe como archivo real.
4. Toda HU tiene al menos un criterio de aceptación Given/When/Then.
5. `traceability.md` tiene exactamente una fila por HU no retirada, sin
   filas huérfanas.
6. Existe al menos un evento `advisor_note` de categoría
   `sugerencia_transversal` logueado antes del cierre del paso `epics` — el
   Asesor tiene que haber revisado y sugerido capacidades transversales
   típicas, aunque el usuario las haya rechazado todas; lo que no puede
   faltar es que la revisión haya ocurrido.

Verificaciones de juicio (requieren lectura semántica del agente auditor):

7. Cada Épica tiene una meta de negocio trazable a un objetivo explícito del
   PRD (sin épicas "flotantes" fuera del alcance declarado).
8. No hay contradicciones entre criterios de aceptación de HU distintas
   dentro de la misma épica (ej. dos reglas de negocio incompatibles sobre
   el mismo campo/entidad).
9. El alcance declarado en el PRD no tiene huecos evidentes respecto a las
   épicas creadas (cobertura), ni las épicas se salen del alcance declarado
   (scope creep).

Las verificaciones 1–6 se ejecutan como chequeo determinístico (ver abajo);
las 7–9 (renumeradas: antes 6–8) quedan a cargo del paso de auditoría
semántica (agente separado o autocrítica, según lo defina el núcleo).

## Extensión del CLI del núcleo

Se agrega un subcomando `factory validate requirements` (extiende el CLI
definido en el spec del núcleo) que corre las verificaciones estructurales
1–6 de forma determinística sobre `docs/requirements/` y `.factory/log.jsonl`
(para la verificación 6) y devuelve una lista de problemas encontrados
(vacía si todo bien). La skill instruye al agente a correr este comando
como primer paso de cada iteración del loop de auditoría, antes de la
revisión semántica — más barato y confiable que pedirle al LLM que
verifique referencias cruzadas a mano.

## Manejo de errores / casos borde

- HU sin épica asignada: error de validación estructural, no se permite
  frontmatter `epica` vacío.
- Referencia circular en `depende_de` (HU-1.1 depende de HU-1.2 que depende
  de HU-1.1): el chequeo estructural la detecta y la reporta como hallazgo
  bloqueante, no queda como advertencia silenciosa.
- Usuario pide avanzar a Arquitectura sin pasar el gate: la skill se niega y
  explica qué falta (lista de hallazgos pendientes), no avanza "por
  cortesía".

## Testing

pytest, cero IO externo, fixtures de árbol de documentos en `tmp_path`:

- `test_validate_requirements.py`: casos positivos (set completo y
  coherente) y cada caso negativo de la checklist estructural 1–6 por
  separado (HU huérfana, dependencia inexistente, referencia circular, fila
  de trazabilidad faltante/huérfana, HU sin criterios de aceptación, cierre
  de `epics` sin evento `advisor_note` de sugerencia transversal).

## Preguntas abiertas para specs futuros

- La verificación de "gaps entre fases" (Requerimientos vs Arquitectura) no
  se puede completar hasta que exista el spec de Arquitectura — este spec
  solo cubre coherencia interna de Requerimientos. El spec de Arquitectura
  debe definir su propio chequeo de cobertura contra `traceability.md`.
