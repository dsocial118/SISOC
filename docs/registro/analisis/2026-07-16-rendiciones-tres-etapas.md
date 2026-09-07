# Análisis: incorporación de tres etapas en el flujo de rendición de cuentas

**Fecha:** 2026-07-16  
**Contexto:** propuesta funcional para evolucionar el flujo actual de rendiciones de cuentas final, manteniendo compatibilidad con la implementación existente en el módulo de rendición final.

---

## 1. Resumen ejecutivo

El flujo actual ya implementa una primera revisión documental por parte del equipo Territorial. En el código actual, esa lógica vive alrededor de los modelos y vistas del módulo de rendición final, donde cada documento tiene estados como "No presentado", "En análisis", "Subsanar" y "Validado".

La propuesta más simple y compatible es mantener ese ciclo documental existente y añadir un nivel superior de control por rendición, que orqueste tres etapas:

1. Revisión de documentación cargada (Territorial)
2. Revisión de la rendición de cuentas (Auditoría)
3. Auditoría administrativa del proceso

La idea central es no duplicar la lógica de observaciones y correcciones; se reutiliza la lógica actual de documentos para las dos primeras etapas y se agrega un estado de proceso a la rendición como capa de coordinación.

---

## 2. Propuesta de modelo de estados

### Recomendación principal

Se recomienda usar un modelo basado en dos niveles:

- una etapa de proceso en la rendición;
- un subestado dentro de esa etapa.

Esto permite una solución simple, escalable y fácil de consumir desde backend, frontend y PWA.

### Campos sugeridos en la entidad Rendición

Agregar a la entidad de rendición, por ejemplo, en el modelo de la rendición final:

- `etapa_proceso`: indica en qué etapa se encuentra la rendición
- `subestado_proceso`: indica el estado concreto dentro de esa etapa

### Valores propuestos

#### Etapa

- `revision_documentacion`: Etapa 1, revisión documental territorial
- `revision_auditoria`: Etapa 2, revisión de la rendición por Auditoría
- `auditoria`: Etapa 3, auditoría administrativa

#### Subestado

- `pendiente`: aún no comenzó la etapa o está esperando pasar a la siguiente fase
- `en_curso`: la etapa está activa
- `pendiente_correcciones`: el usuario debe corregir documentos observados
- `finalizada`: la etapa terminó correctamente
- `finalizada_con_observaciones`: la etapa terminó con observaciones registradas

### Estados visibles recomendados para la UI

- `Etapa 1 en curso`
- `Etapa 1 finalizada, pendiente de revisión de Auditoría`
- `Etapa 2 en curso`
- `Etapa 2 pendiente de correcciones`
- `Etapa 2 finalizada, pendiente de auditoría administrativa`
- `Auditoría en curso`
- `Auditoría finalizada sin observaciones`
- `Auditoría finalizada con observaciones`

### Transiciones sugeridas

1. Al crear o cargar la rendición:
   - `revision_documentacion + pendiente`

2. Cuando Territorial empieza a revisar:
   - `revision_documentacion + en_curso`

3. Cuando todos los documentos están aprobados y se finaliza la Etapa 1:
   - `revision_auditoria + pendiente`
   - además se marca la rendición como lista para Auditoría

4. Cuando Auditoría inicia la revisión:
   - `revision_auditoria + en_curso`

5. Si Auditoría observa documentos:
   - `revision_auditoria + pendiente_correcciones`

6. Cuando el usuario corrige y vuelve a presentar:
   - `revision_auditoria + en_curso`

7. Cuando Auditoría aprueba la rendición y finaliza la Etapa 2:
   - `auditoria + pendiente`

8. Cuando la auditoría administrativa comienza:
   - `auditoria + en_curso`

9. Al cerrar la auditoría:
   - `auditoria + finalizada` o `auditoria + finalizada_con_observaciones`

### Justificación

Esta propuesta evita sobrecargar el modelo de documentos con lógica de negocio de etapa y permite mantener la semántica del flujo actual sin romper la implementación ya desarrollada.

---

## 3. Cambios necesarios en backend

### 3.1 Modelo de rendición

Agregar a la entidad de rendición final:

- `etapa_proceso`
- `subestado_proceso`
- opcionalmente, si se quiere trazabilidad de artefactos:
  - `pdf_path` o `archivo_pdf`
  - `pdf_version`
  - `pdf_generado_en`

### 3.2 Servicio de negocio

Crear o extender un servicio de rendición con métodos como:

- `finalizar_etapa_1(rendicion)`
- `iniciar_etapa_2(rendicion)`
- `finalizar_etapa_2(rendicion)`
- `iniciar_etapa_3(rendicion)`
- `finalizar_etapa_3(rendicion, con_observaciones=False, detalle=None)`
- `regenerar_pdf(rendicion)`
- `obtener_rendiciones_para_auditoria(user)`

### 3.3 Reutilización de la lógica actual

No conviene reimplementar el circuito de observaciones desde cero. La propuesta contempla reutilizar:

- la misma tabla o modelo de documentos;
- el mismo campo de observaciones;
- los mismos endpoints de validación y subsanación;
- el mismo flujo de carga y reemplazo de archivos.

Lo que cambia es el contexto: el mismo documento puede pasar por la Etapa 1 y luego por la Etapa 2, sin cambiar el mecanismo de revisión.

### 3.4 Regeneración del PDF

Se recomienda que el PDF se regenere en dos momentos clave:

1. al finalizar la Etapa 1, con la documentación aprobada hasta ese momento;
2. al volver a aprobar un documento en la Etapa 2, o al finalizar la Etapa 2, para asegurar que el PDF refleje siempre la última versión aprobada.

### 3.5 Versionado del PDF

Para evitar reemplazos ambiguos, se recomienda:

- reemplazar el PDF anterior por una nueva versión del mismo artefacto;
- incrementar un contador `pdf_version`;
- registrar en historial el cambio de PDF.

Esto es más simple que conservar múltiples PDFs históricos y da suficiente trazabilidad para la operación.

---

## 4. Cambios necesarios en frontend/UI

### 4.1 En la vista de detalle de la rendición

Mostrar:

- un badge o chip con la etapa actual;
- un texto explicativo del estado de la rendición;
- acciones según el rol y la etapa actual.

### 4.2 En el listado para Territorial

Agregar una advertencia visual cuando la rendición pasó a la etapa de espera para Auditoría, por ejemplo:

- badge: "Pendiente de revisión de Auditoría"
- notificación o alerta en el detalle de la rendición

### 4.3 En el listado para Auditoría

Crear una vista o filtro específico para mostrar únicamente las rendiciones que estén en:

- `revision_auditoria + pendiente`
- `revision_auditoria + en_curso`
- `revision_auditoria + pendiente_correcciones`

### 4.4 Acciones en UI

- `Finalizar Etapa 1`
- `Iniciar revisión de Auditoría`
- `Aprobar Etapa 2`
- `Solicitar correcciones`
- `Iniciar Auditoría administrativa`
- `Finalizar Auditoría sin observaciones`
- `Finalizar Auditoría con observaciones`

### 4.5 Compatibilidad con la UI actual

No es necesario reescribir la interfaz completa. Se puede integrar la nueva lógica como una capa adicional sobre la vista de detalle actual, sin romper los flujos de revisión documental existentes.

---

## 5. Cambios necesarios en la PWA

La PWA no necesita un rediseño completo del flujo, porque el mecanismo actual de carga y corrección de documentos ya tiene el comportamiento deseado.

### Cambios recomendados

1. Mostrar el estado de la rendición en la PWA
   - por ejemplo: "Pendiente de revisión por Auditoría"
   - o "Requiere correcciones"

2. Mostrar observaciones de Auditoría de forma explícita
   - reutilizando el mismo concepto de observaciones disponible hoy

3. Permitir volver a cargar o reemplazar documentos observados
   - sin introducir un flujo distinto al actual

4. Notificar cuando una rendición pasó a una nueva etapa
   - idealmente mediante el mecanismo de mensajes o notificaciones ya existente en la PWA

### Recomendación de implementación

Se recomienda reutilizar la lógica actual de carga y reemplazo de documentos, y simplemente exponer en la interfaz de la PWA un contexto extra de etapa y observaciones. Esto minimiza el impacto y evita duplicar el flujo de corrección.

---

## 6. Migraciones de base de datos

### Migración mínima

Agregar campos a la entidad de rendición:

- `etapa_proceso`
- `subestado_proceso`

### Migración recomendada

Si se quiere robustecer el artefacto final, agregar también:

- `archivo_pdf`
- `pdf_version`
- `pdf_generado_en`

### Valor por defecto para datos existentes

Para registros ya creados, se recomienda un valor por defecto seguro:

- `etapa_proceso = revision_documentacion`
- `subestado_proceso = pendiente`

Y, si corresponde, un backfill manual para rendiciones ya aprobadas completamente en el flujo actual.

---

## 7. Reutilización de la lógica existente

La implementación actual ya resuelve bien la parte más delicada del flujo: la revisión documental y las observaciones sobre documentos. Por ello, la propuesta recomienda no reemplazar esa lógica, sino encapsularla y extenderla.

### Lógica ya existente que conviene preservar

- validation of document statuses
- observation flow
- correction and replacement of files
- history/traceability of document actions

### Qué conviene abstraer

Crear un servicio o capa intermedia que:

- reciba el documento y la etapa actual;
- decida si el cambio debe impactar solo el documento o también la rendición;
- dispare la regeneración del PDF cuando corresponda.

### Beneficio

Esto evita duplicar código y conserva la coherencia con la implementación actual del módulo.

---

## 8. Riesgos técnicos y casos borde

### 8.1 Documentos incompletos al finalizar Etapa 1

Riesgo: se podría marcar la etapa como finalizada con documentos aún sin aprobar.  
Mitigación: bloquear la transición si existe algún documento que no esté en estado `Validado`.

### 8.2 PDF desactualizado

Riesgo: el PDF queda viejo si se corrige un documento después de haberlo generado.  
Mitigación: regenerarlo en cada cambio relevante y guardarlo como versión nueva.

### 8.3 Correcciones repetidas

Riesgo: un documento puede volver a observación varias veces.  
Mitigación: mantener el mismo circuito de observaciones y permitir múltiples vueltas sin cambiar la lógica base.

### 8.4 Permisos y roles

Riesgo: Territorial y Auditoría podrían ver o actuar sobre los mismos recursos de forma ambigua.  
Mitigación: separar filtros y acciones por rol desde el backend y reforzarlos en la UI.

### 8.5 Datos previos a la migración

Riesgo: registros antiguos podrían quedar sin estado explícito.  
Mitigación: definir defaults seguros y, si es necesario, aplicar un backfill basado en el estado documental actual.

---

## 9. Propuesta de implementación incremental

Para minimizar impacto en producción, se recomienda implementar en fases.

### Fase 1 - Introducción del estado de proceso

Objetivo: incorporar la capa de etapas sin romper el flujo actual.

Cambios:

- agregar `etapa_proceso` y `subestado_proceso`;
- mantener el flujo documental intacto;
- mostrar badge de estado en la UI;
- agregar transición de Etapa 1 a pendiente de Auditoría.

### Fase 2 - Integración del flujo de Auditoría

Objetivo: habilitar la revisión por Auditoría reutilizando el mismo mecanismo actual.

Cambios:

- crear listado filtrado para Auditoría;
- permitir aprobar o solicitar correcciones;
- reusar el mismo circuito de observaciones y carga de documentos.

### Fase 3 - Auditoría administrativa y PDF

Objetivo: cerrar el proceso completo.

Cambios:

- agregar estados de auditoría administrativa;
- habilitar acciones de inicio y cierre de la Etapa 3;
- regenerar y versionar el PDF automáticamente.

### Beneficio de esta ruta

- evita un cambio complejo de una sola vez;
- permite validar el nuevo flujo con menos riesgo;
- mantiene compatibilidad con la implementación actual y con la experiencia de usuario existente.

---

## 10. Recomendación final

La propuesta más robusta y compatible es la siguiente:

- conservar el modelo de documentos y su lógica actual como motor de revisión documental;
- agregar un estado de proceso por rendición para coordinar las tres etapas;
- reutilizar el mismo flujo de observaciones, subsanación y carga de archivos en Etapa 2;
- agregar una capa visual de estado y advertencias en UI y PWA;
- introducir la regeneración del PDF como parte del cierre de etapas y de las correcciones de documentos.

Esta arquitectura es simple, fácil de mantener y permite escalar sin duplicar lógica ni romper el flujo actual.
