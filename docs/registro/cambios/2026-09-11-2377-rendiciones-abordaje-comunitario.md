# Issue #2377 — Requerimientos PWA/SISOC de Abordaje Comunitario (backend y backoffice)

Fecha: 2026-09-11

Alcance de este registro: los cambios de **SISOC**. El frontend de la PWA se
implementa en el repositorio `dsocial118/Espacios-Comunitarios` y el issue no se
cierra hasta que ambos estén integrados y validados en conjunto.

Decisiones que el issue dejaba abiertas:
[`2026-09-11-2377-rendiciones-secuencia-acta-visualizacion.md`](../decisiones/2026-09-11-2377-rendiciones-secuencia-acta-visualizacion.md).

## Qué cambió

### 1. Número de rendición secuencial (punto 2 del issue)

La validación de unicidad dentro de proyecto + convenio se amplía: el número
debe ser además el **siguiente de la secuencia**. Si el último es 2, el único
valor aceptado es 3.

- Regla única en `RendicionCuentaMensualService._validar_numero_y_periodo`,
  usada por el alta PWA, la edición PWA y el formulario web. No vive en la PWA.
- `siguiente_numero_rendicion()` expone el valor esperado.
- La asignación se serializa con `select_for_update()` sobre la fila ancla del
  scope, dentro de la transacción que crea o edita.
- Editar sin cambiar el número no revalida la secuencia; cambiarlo sí.

### 2. Período de tres meses para Línea Secos (punto 3)

`Fecha Fin` puede llegar hasta el último día del tercer mes calendario contado
desde el mes de `Fecha Inicio` (03/09 → 30/11). Las demás líneas conservan la
validación mensual. El cálculo usa `calendar.monthrange`, no una cantidad fija
de días, así que febrero y los años bisiestos salen correctos.

El error se devuelve en el campo `periodo_fin`.

### 3. Catálogo documental por línea programática (punto 4)

`Planilla de Seguros` sale del listado de documentos a gestionar de las
rendiciones de **Línea Secos**. Se implementa con la clave `lineas` en
`DocumentacionAdjunta.CATEGORIAS_CONFIG`, no borrando la categoría.

- No se borran documentos ni archivos históricos: una rendición Secos que ya
  tenga un `planilla_seguros` cargado lo sigue mostrando, vía
  `RendicionCuentaMensualService.obtener_categorias_visibles`.
- Web y API usan esa misma función, así que no pueden dar catálogos distintos.
- Adjuntar o solicitar `planilla_seguros` en Secos queda rechazado.
- Línea Tradicional no cambia.

### 4. Etiquetas de documentos (punto 10)

Solo texto visible; los `codigo` persistidos no cambian y no hay migración de
datos:

- `comprobantes_alimentario`: → `Facturas y Tickets Prestación Alimentaria`
- `comprobantes_siph`: → `Facturas y Tickets SIPH`

### 5. `Revisión de Auditoría` → `Revisión para Carga` (punto 5)

Cambia únicamente la denominación visible de la etapa `revision_auditoria`:
grilla, detalle, filtros y grilla de avance del legajo de organización.

- El valor persistido `revision_auditoria` **no cambia**.
- La constante `ETAPA_REVISION_AUDITORIA` y los nombres de permisos no cambian.
- La etapa independiente `auditoria` (`Auditoría`) no se toca.
- Los `value` del filtro `Estado` siguen siendo los mismos.

La PWA debe seguir distinguiendo el estado interno por `etapa_proceso` +
`subestado_proceso`, nunca por la etiqueta.

### 6. Confirmación automática de visualización de documentos (punto 6)

Al abrir un documento con el botón «Ver» en el detalle de la rendición se
registra automáticamente la visualización. No hay acción manual de confirmar.

Persistencia mínima: tres campos nuevos en `DocumentacionAdjunta`
(`visualizacion_etapa`, `visualizacion_usuario`, `visualizacion_fecha`). No hay
historial: cada registro pisa al anterior.

Contrato funcional implementado:

- la confirmación pertenece al par **documento + etapa vigente**, no al usuario;
- alcanza con que la registre un usuario con el permiso de la etapa vigente;
  quien tiene permiso de otra etapa puede ver el archivo pero **no** confirma;
- el botón «Ver» pasa a servirse por Django
  (`rendicioncuentasmensual/documento/<pk>/ver/`), con el mismo control de
  acceso que el detalle. Antes apuntaba directo a la URL de media, sin ninguna
  comprobación de permisos;
- el archivo se abre **antes** de confirmar: un documento inexistente o una
  descarga fallida devuelven 404 y no dejan nada confirmado;
- validar un documento no altera la confirmación;
- enviarlo a subsanar tampoco la altera;
- cuando un documento subsanado se reemplaza y vuelve a presentado, se resetea
  únicamente la confirmación de ese documento;
- cuando `RendicionProcesoService` finaliza una etapa y avanza a la siguiente, se
  resetean todas las confirmaciones de la rendición, sin importar el estado
  individual de cada documento, dentro de la misma transacción que el avance;
- no se implementa retroceso de etapa porque el flujo no lo contempla.

En la interfaz, junto al botón «Ver» aparece «Visualizado» —con quién y cuándo en
el `title`— o «Sin visualizar».

Documentos existentes: los tres campos quedan en `NULL`, es decir no visualizado.
Sin backfill.

### 7. Proyecto como filtro predeterminado (punto 7)

El listado global preselecciona `Proyecto` en el selector de campo. Antes la fila
arrancaba en el placeholder «Buscar por» y al enviar caía igual en Proyecto: el
cambio hace visible esa elección para que se pueda interactuar directo con el
filtro.

- `get_filters_ui_config()` expone `defaultField`; `advanced_filters.js` lo aplica
  solo si viene, así que los otros 45 listados no cambian.
- Los demás filtros, la paginación, el ordenamiento y los favoritos siguen igual.
- No se aplica foco automático, para no robarle el foco ni el scroll a quien usa
  teclado o lector de pantalla.

### 8. Edición web de datos generales (punto 11)

**Causa raíz del «se muestra todo en blanco»**, confirmada reproduciéndola y no
inferida: `RendicionDatosForm` declaraba los períodos como
`forms.DateInput(attrs={"type": "date"})` sin `format`, así que Django
renderizaba `value="01/08/2026"`. Un `<input type="date">` solo acepta un value
ISO `aaaa-mm-dd` y descarta cualquier otra cosa, dejando el campo vacío. Como
además ambos campos eran obligatorios, no se podía guardar sin volver a
tipearlos. `convenio` y `numero_rendicion` **sí** se precargaban bien.

Cambios:

- `format="%Y-%m-%d"` en los dos widgets de fecha: la precarga ahora funciona;
- ningún campo es obligatorio para guardar;
- semántica de actualización parcial explícita: un campo vacío conserva el valor
  persistido; `nombre` es la excepción y sí se puede limpiar a propósito, porque
  es opcional en el modelo. No se construye un diccionario incompleto que borre
  información;
- la edición aplica **las mismas reglas de dominio que el alta** —convenio,
  número, secuencia y período, incluida la ventana de tres meses de Línea
  Secos— delegando en `RendicionCuentaMensualService.validar_datos_generales`,
  con `excluir_pk` para no chocar consigo misma y `numero_actual` para no exigir
  la secuencia cuando el número no cambia;
- los errores de dominio se vuelcan por campo; la clave `periodo`, que no es un
  campo del formulario, va a errores no asociados a campo;
- el POST completo corre dentro de `transaction.atomic`: la validación toma el
  bloqueo de numeración, así que validar y guardar tienen que compartir
  transacción para que el bloqueo proteja algo;
- `mes`/`anio` solo se recalculan si hay `periodo_inicio`, porque una rendición
  histórica puede no tener período.
- Permisos y alcance sin cambios: sigue exigiendo
  `rendicioncuentasmensual.edit_rendicion_data`.

### 9. Acta de Auditoría (punto 12)

**12.1 — El acta deja de ser obligatoria para todos los programas.** Se quitó la
validación del formulario. Además, `acta_auditoria` solo se asigna si llega un
archivo: guardar sin adjuntar **conserva** el acta ya cargada, no la borra.
Ningún archivo histórico se elimina.

**12.2 — Línea Secos** conserva el flujo actual salvo esa opcionalidad. No pide
el selector Sí/No y rechaza explícitamente `rendiciones_incluidas`.

**12.3 — Línea Tradicional**, al finalizar la auditoría:

- `monto_rendido` obligatorio, `monto_observado` opcional;
- `genera_acta_auditoria` (Sí/No) obligatorio;
- con **No** se finaliza sin seleccionar rendiciones;
- con **Sí** se habilita el selector múltiple `Indique rendiciones incluidas`,
  que es opcional (ver decisión registrada);
- cada opción se muestra como `Proyecto - Convenio - Número de rendición - Período`;
- después continúan el Resultado de Auditoría y las Observaciones ya existentes,
  y el flujo posterior no cambia.

Campos nuevos en `RendicionCuentaMensual`: `monto_observado`,
`genera_acta_auditoria` (nullable: `NULL` = no respondido, cubre históricos y
Secos) y el M2M autorreferencial `rendiciones_incluidas`.

Integridad:

- elegibles = mismo scope de proyecto + `linea_programatica = tradicional` +
  `genera_acta_auditoria = False` + distintas de sí misma. Autorreferencia, otro
  proyecto y «rendición que genera su propia acta» quedan excluidas por
  construcción del queryset, no por comprobaciones sueltas;
- `ModelMultipleChoiceField` valida pertenencia **y** el servicio revalida contra
  el mismo queryset antes de asociar: no se confía en lo que manda el navegador;
- el `.set()` del M2M ocurre dentro de la transacción de
  `RendicionProcesoService.ejecutar`, después del `save()`: ante una selección
  inválida no queda persistido ni el monto ni el subestado;
- los duplicados los descarta el propio `.set()`;
- las asociaciones históricas no se borran si después cambia la elegibilidad: la
  validación es al momento de asociar, no retroactiva;
- `_validar_estado` solo admite finalizar desde `en_curso`, así que la asociación
  se define una única vez.

### 10. Edición de datos desde la PWA (punto 13)

Nuevo `PATCH /api/comedores/{id}/rendiciones/{rendicion_id}/`, sobre la misma
action que ya servía el `GET`. El contrato de lectura no cambia.

- Solo con `estado == "elaboracion"`; en cualquier otro estado responde `409`
  con el estado actual, sin escribir nada.
- Corre bajo `transaction.atomic` con `select_for_update()` sobre la rendición y
  relee el estado ya con el bloqueo tomado: si la etapa cambió mientras llegaba
  la edición, gana el `409`.
- Permisos idénticos a los del alta: representante del espacio con
  `manage_mobile_rendicion`; el coordinador PWA es de solo lectura.
- Actualización parcial real vía serializer `partial=True`: lo omitido conserva
  su valor, no se arma un diccionario completo a mano.
- Reutiliza `validar_datos_generales`, con `excluir_pk` y `numero_actual`, así
  que aplican exactamente las mismas reglas de convenio, secuencia y período que
  en el alta y en el formulario web.
- Errores de dominio por campo bajo `detail`, igual que el `POST` de alta: la
  PWA parsea un solo formato.
- Campos protegidos (`estado`, `etapa_proceso`, `linea_programatica`,
  `proyecto`, montos, acta, fechas) se ignoran si llegan y quedan intactos.
- `mes`/`anio` se recalculan cuando cambia el período y se registra
  `usuario_ultima_modificacion`.

Además, el `GET` de detalle suma el bloque aditivo `reglas_datos_generales`
(convenios válidos, rango del número, próximo número por convenio y meses de la
ventana de período) para que la PWA arme el formulario y sus alertas de los
puntos 2 y 3 del issue sin reimplementar la regla. El próximo número se calcula
delegando en `siguiente_numero_rendicion`, de modo que sea exactamente el mismo
valor que el servidor va a exigir después.

### 11. Health-check para la PWA (punto 9)

`GET /api/pwa/health/` pasa a verificar también la base de datos:

| Situación | HTTP | Cuerpo |
| --- | --- | --- |
| Disponible | `200` | `{"status": "ok", "database": "ok"}` |
| Base caída | `503` | `{"status": "unavailable", "database": "unavailable"}` |

Sigue siendo público (`AllowAny`), no expone detalle interno del error y no
incorpora RENAPER. **No** verifica el storage de archivos, así que un `200` no
garantiza que una carga con adjunto se complete; la limitación está escrita en el
contrato para no prometer de más.

`GET /health/` queda intacto como sonda de infraestructura (texto plano `OK`).

Contrato completo para la PWA:
[`docs/implementaciones/pwa_backend.md`](../../implementaciones/pwa_backend.md).

## Puntos que se resuelven en Espacios-Comunitarios

No se implementan en SISOC y no deben darse por cerrados hasta que su PR esté
integrado:

- botón `Crear Rendición` → `Rendiciones` (punto 1);
- alertas visuales de secuencia y período (puntos 2 y 3);
- `Subsanación solicitada por equipo Territorial` / `por equipo de Auditoría`
  (punto 8);
- modal bloqueante de conectividad (punto 9);
- formulario visual de edición de datos generales (punto 13).

SISOC aporta para esos puntos los estados internos, las validaciones, los
endpoints y los errores por campo.

## Migraciones

Tres migraciones, todas aditivas y reversibles, sin backfill y sin renombrar
ningún valor persistido. Se aplican en orden:

| Migración | Contenido | Efecto sobre datos |
| --- | --- | --- |
| `0020_issue_2377_etiquetas_catalogo` | `AlterField` de choices en `documentacionadjunta.categoria`, `solicituddocumentofaltante.categoria` y `rendicioncuentamensual.etapa_proceso` | Ninguno: solo cambian las etiquetas. En MySQL un `AlterField` de choices sobre un `CharField` no reescribe la tabla |
| `0021_issue_2377_visualizacion_documentos` | `AddField` de `visualizacion_etapa`, `visualizacion_usuario`, `visualizacion_fecha` en `DocumentacionAdjunta` | Los documentos existentes quedan en `NULL` = no visualizado |
| `0022_issue_2377_acta_auditoria` | `AddField` de `monto_observado` y `genera_acta_auditoria`, más la tabla intermedia de `rendiciones_incluidas` | Las rendiciones existentes quedan con `NULL` = no respondido y sin rendiciones asociadas |

No se agregaron índices ni constraints nuevos. En particular **no** se agregó un
`UniqueConstraint` para la secuencia del número de rendición: el motivo está en
la decisión 3 del registro de decisiones.

## Despliegue y rollback

### Orden de despliegue

1. Aplicar `0020`, `0021` y `0022` en ese orden.
2. Desplegar SISOC. Los tres cambios de esquema son aditivos, así que la versión
   anterior del código convive con el esquema nuevo: las columnas agregadas son
   nullables y nadie las lee.
3. Desplegar el PR de `Espacios-Comunitarios` **después**. SISOC queda
   compatible hacia atrás con la PWA actual: `PATCH` y `reglas_datos_generales`
   son aditivos y el contrato de lectura no cambió.

La secuencia inversa (PWA primero) no sirve: la PWA nueva depende del `PATCH` y
del bloque de reglas, que todavía no existirían.

### Rollback

- **Código**: volver al commit anterior. Las tres columnas nuevas quedan en la
  base sin que nadie las lea; no corrompen documentos ni estados del proceso.
  Las confirmaciones de visualización y las decisiones de acta simplemente dejan
  de mostrarse.
- **Migraciones**: las tres son reversibles
  (`migrate rendicioncuentasmensual 0019`). Revertir `0022` descarta las
  asociaciones de rendiciones incluidas y los valores de
  `genera_acta_auditoria`/`monto_observado`; revertir `0021` descarta las
  confirmaciones de lectura. En ambos casos se pierde información nueva, no
  información previa al cambio. Revertir `0020` solo restaura etiquetas.
- Lo habitual es **revertir el código sin revertir las migraciones**: es
  suficiente, no pierde datos y evita un `ALTER TABLE` de urgencia.

### Riesgos conocidos

- La serialización del número de rendición se apoya en `select_for_update()`,
  que sobre SQLite (tests) es un no-op: la protección real solo se ejercita en
  MySQL y no se validó contra una base MySQL en esta entrega.
- Los documentos ahora se sirven por Django (`FileResponse`) en vez de por la URL
  de media directa. Gana control de acceso —antes no había ninguno— pero un
  archivo muy grande ocupa un worker de aplicación mientras se transmite. Si
  aparece presión, la salida es delegar la entrega a NGINX con `X-Accel-Redirect`.
- El selector de rendiciones incluidas materializa todas las elegibles del
  proyecto. Con los volúmenes actuales es razonable; si un proyecto creciera
  mucho habría que evaluar búsqueda remota o paginación, que hoy nadie pidió.
