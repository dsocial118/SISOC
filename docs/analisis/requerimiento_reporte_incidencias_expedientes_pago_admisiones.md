# Requerimiento funcional: Reporte de incidencias de vinculación Expedientes de Pago ↔ Admisiones

**Fecha:** 28 de agosto de 2026
**Estado:** Requerimiento funcional (sin implementación)
**Alcance del documento:** define las reglas de negocio del matcheo automático y los requisitos funcionales del módulo de reporte de incidencias. No es un diseño técnico ni una guía de implementación.

---

## 1. Contexto

Un desarrollador está trabajando en integrar la carga de **expedientes de pago** (app `expedientespagos`) con **admisiones** (app `admisiones`), usando el número de expediente como campo común para vincular cada expediente de pago con la admisión a la que corresponde.

Relevamiento del estado actual del código, como evidencia de partida:

- Hoy **no existe ningún vínculo de datos** entre `ExpedientePago` y `Admision`. El único vínculo relacional que tiene `ExpedientePago` es `comedor` (FK a `Comedor`, `on_delete=SET_NULL`, nullable) — `expedientespagos/models.py:39-44`.
- `ExpedientePago` tiene dos campos de expediente: `expediente_convenio` (obligatorio) y `expediente_pago` (opcional) — `expedientespagos/models.py:8-14`.
- `Admision.num_expediente` es un `CharField` **sin `unique`** a nivel de modelo ni de base de datos — `admisiones/models/admisiones.py:186`.
- La falta de unicidad de `num_expediente` ya generó un incidente real en producción: el issue #2272 detectó admisiones con el mismo número de expediente ocupado por más de un registro, resuelto de forma manual y puntual con un comando (`admisiones/management/commands/corregir_expedientes_issue_2272.py`) contra un CSV auditado (ver `docs/operacion/correccion_expedientes_issue_2272.md`). Esto confirma que el escenario "más de una admisión con el mismo número de expediente" es un caso real, no hipotético.

De la naturaleza de estos dos campos (texto libre, sin validación de unicidad) se desprende que el matcheo automático entre un expediente de pago y su admisión puede no resolverse de forma directa en todos los casos. El presente requerimiento cubre cómo se detectan y gestionan esos casos.

---

## 2. Objetivo

Definir:

1. La regla de matcheo automático entre un expediente de pago y una admisión.
2. Qué se considera una **incidencia** de vinculación.
3. Los requisitos funcionales del **módulo de reporte de incidencias**: listado, filtros, resolución manual y reprocesamiento.

---

## 3. Reglas de negocio del matcheo

### 3.1 Campos comparados

Se compara `ExpedientePago.expediente_convenio` contra `Admision.num_expediente`.

`ExpedientePago.expediente_pago` **no** interviene en el matcheo.

### 3.2 Alcance de la búsqueda

La búsqueda de admisiones candidatas se restringe a las admisiones del **mismo comedor** que el expediente de pago (`Admision.comedor == ExpedientePago.comedor`). No se buscan candidatas en otros comedores.

**Caso sin comedor:** si `ExpedientePago.comedor` es nulo (el campo es opcional), ese expediente de pago queda **fuera del alcance de este módulo**. No se procesa como incidencia; se asume que todo expediente de pago relevante para este flujo tiene comedor cargado.

### 3.3 Tipo de comparación

La comparación es **exacta** (igualdad de string), sin normalización de formato (sin trim, sin ajuste de mayúsculas/minúsculas, sin ajuste de ceros a la izquierda ni de separadores). Dos valores que difieran en formato aunque representen el mismo expediente no matchean.

### 3.4 Resultado del matcheo

Para cada expediente de pago con comedor cargado, se buscan admisiones del mismo comedor cuyo `num_expediente` sea exactamente igual a `expediente_convenio`:

| Cantidad de admisiones candidatas | Resultado |
|---|---|
| Exactamente 1 | Vínculo automático directo. No es una incidencia. |
| 0 | Incidencia de tipo **"sin match"**. |
| 2 o más | Incidencia de tipo **"múltiples matches"**. |

No se definen otros tipos de incidencia (por ejemplo, `expediente_convenio` vacío, o admisión candidata en un estado no válido) — quedan explícitamente fuera de alcance de esta primera versión.

---

## 4. Persistencia del vínculo

El vínculo entre `ExpedientePago` y su `Admision` correspondiente se **persiste** (no se calcula al vuelo cada vez que se consulta). El desarrollador define el diseño de datos concreto; como referencia de precedente en el repo, el módulo `celiaquia.RegistroErroneo` (`celiaquia/models.py:622-645`) resuelve un problema estructuralmente similar (registros pendientes de asociación, con `procesado`, `mensaje_error`, listado + edición individual + reproceso masivo — `celiaquia/views/expediente.py:1467, 2383, 2452, 2692`) y puede tomarse como precedente de diseño.

El registro de la incidencia debe permitir guardar, como mínimo:

- Tipo de incidencia (sin match / múltiples matches).
- Estado (pendiente / resuelta).
- Las admisiones candidatas, cuando el tipo es "múltiples matches".
- Trazabilidad de la resolución: usuario que la resolvió, fecha/hora, y si fue por selección manual o por reprocesamiento automático (ver punto 6).

---

## 5. Resolución de incidencias

### 5.1 Caso "sin match" (0 candidatas)

No hay admisión para elegir. Se resuelve únicamente corrigiendo el dato de origen (el `num_expediente` de alguna admisión, o el `expediente_convenio` del expediente de pago) y reprocesando.

### 5.2 Caso "múltiples matches" (2+ candidatas)

El usuario puede resolver la incidencia de dos formas:

1. **Selección manual**: desde el módulo de incidencias, elige explícitamente cuál de las admisiones candidatas es la correcta. Esa elección queda registrada (usuario, fecha/hora, método = "manual").
2. **Corrección en origen + reproceso**: se corrige el dato que genera la ambigüedad (por ejemplo, se corrige el `num_expediente` duplicado en una de las admisiones) y se reprocesa: si a partir de la corrección queda una única candidata, se vincula automáticamente (método = "automático").

Ambas vías están disponibles; no son excluyentes.

---

## 6. Reprocesamiento

El reproceso de un expediente de pago pendiente (para volver a evaluar si ya matchea) puede dispararse de dos formas, no excluyentes:

1. **Automático**: al guardarse un cambio en `num_expediente` de una `Admision`, se dispara el reproceso de los expedientes de pago pendientes del mismo comedor.
2. **Manual**: desde el módulo de incidencias, el usuario dispara el reproceso —individual o masivo— cuando lo necesite (por ejemplo, después de una carga masiva de admisiones o de expedientes de pago).

---

## 7. Módulo de reporte de incidencias — requisitos funcionales

### 7.1 Listado

Debe mostrar los expedientes de pago con incidencia pendiente (y, según decisión de UX del desarrollador, también las ya resueltas si se habilita el filtro de estado).

### 7.2 Filtros

El listado debe permitir filtrar como mínimo por:

- Comedor.
- Tipo de incidencia (sin match / múltiples matches).
- Rango de fecha de carga del expediente de pago.
- Estado de la incidencia (pendiente / resuelta).
- Expediente de pago (búsqueda por número).
- Organización — usando `Comedor.organizacion` (FK real, `comedores/models.py:295-296`), **no** `ExpedientePago.organizacion_creacion` (campo de texto libre cargado al crear el registro, no vinculado formalmente a `Organizacion`).
- Período del expediente de pago (`mes_convenio` / `ano`).

### 7.3 Acciones desde el listado

- Ver el detalle de una incidencia, incluyendo —cuando aplica— la lista de admisiones candidatas (caso "múltiples matches").
- Resolver manualmente una incidencia de tipo "múltiples matches" seleccionando la admisión correcta.
- Reprocesar una incidencia puntual.
- Reprocesar en forma masiva (sobre el conjunto filtrado o seleccionado).

### 7.4 Trazabilidad

Cada incidencia resuelta debe conservar quién la resolvió, cuándo, y si la resolución fue manual o automática (por reproceso).

---

## 8. Permisos

El módulo se rige por el mismo perfil que ya gestiona expedientes de pago. Hoy ese acceso se controla, en las vistas existentes de `expedientespagos`, mediante `user_has_any_permission_codes` con el código `expedientespagos.view_expedientepago` (ver `expedientespagos/views.py:115-127`). El desarrollador debe definir si reutiliza ese mismo código de permiso para operar el módulo (ver, filtrar, resolver, reprocesar) o si conviene un permiso distinto para la acción de resolver/reprocesar (por ejemplo, un `change` separado de un `view`). Esta definición queda a criterio técnico, respetando que el universo de usuarios habilitados es el mismo que hoy gestiona expedientes de pago.

---

## 9. Fuera de alcance (explícito)

- Normalización de formato del número de expediente (ceros a la izquierda, mayúsculas, espacios): se definió comparación exacta, no normalizada.
- Incidencias por `expediente_convenio` vacío o inválido.
- Incidencias por admisión candidata en un estado no válido (por ejemplo, rechazada o dada de baja): el matcheo no filtra por estado de la admisión.
- Expedientes de pago sin comedor cargado.
- Cualquier cambio al flujo de carga/edición de `ExpedientePago` en sí (formulario, validaciones) más allá de disparar el matcheo.

---

## 10. Puntos abiertos para definición técnica

Estos puntos no bloquean el requerimiento funcional, pero el desarrollador debe resolverlos al implementar:

1. Diseño concreto del modelo de datos para persistir el vínculo y la incidencia (FK directo en `ExpedientePago` + modelo de incidencia separado, o alternativa equivalente).
2. Nombre y alcance exacto del/los permiso(s) Django usados por el módulo (reutilizar `expedientespagos.view_expedientepago` vs. crear uno nuevo para la acción de resolver/reprocesar).
3. Comportamiento y performance del reproceso automático disparado al guardar una `Admision` (volumen esperado de expedientes de pago pendientes por comedor).
4. Diseño de la UI de selección manual de admisión candidata en el caso "múltiples matches".
