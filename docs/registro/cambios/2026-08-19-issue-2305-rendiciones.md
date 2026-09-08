# Issue 2305: evolutivos de rendiciones mensuales

## Alcance

Se coordinó el flujo web y PWA de rendiciones: catálogos cerrados de convenio y
número, período mensual progresivo, categorías múltiples, separación de
comprobantes, confirmación de envío, solicitudes de documentos faltantes,
subsanación ampliada y edición protegida de datos generales.

El listado global incorpora exportación CSV sobre el resultado filtrado,
configuración de columnas, filtro y pill de etapa. La descarga PDF usa un nombre
descriptivo con proyecto, convenio, número y período.

## Datos y compatibilidad

La migración `0017` agrega el nombre de rendición, el permiso
`edit_rendicion_data` y `SolicitudDocumentoFaltante`. Los documentos históricos
de categoría `comprobantes` se migran a `comprobantes_alimentario`.

## Despliegue

Backend y SISOC-Mobile deben publicarse coordinadamente. Aplicar migraciones
antes de desplegar la PWA y validar creación, envío, solicitud de faltante,
subsanación, exportación y edición con/sin permiso.

## Validación local

- Suite focalizada de rendiciones y API PWA: 77 casos exitosos.
- Build TypeScript/Vite y lint focalizado de los archivos PWA: sin errores.
- `black`, `djlint`, chequeo Django y control de migraciones: exitosos.
- La navegación visual integrada quedó pendiente porque el entorno Docker local
  no pudo resolver el host `mysql`; no afecta los checks automatizados.

## Correcciones posteriores a la reapertura

- Durante una subsanación, las categorías que admiten múltiples archivos
  permiten adjuntar documentación nueva sin exigir que reemplace un documento
  observado. Si la carga indica un documento a subsanar, se conservan las
  validaciones y la trazabilidad del reemplazo.
- La edición web de datos generales usa un formulario específico para convenio,
  número, período y nombre. Esto evita que el template general intente renderizar
  campos de documentación que no existen y provoque un `CrispyError`.
- El listado global carga el helper compartido que ejecuta la exportación CSV;
  el botón conserva los filtros activos y deja de quedar sin respuesta al click.
- La configuración de columnas deja el selector local artesanal y adopta el modal
  estándar de SISOC, con preferencias persistidas por usuario, ordenamiento,
  guardado y restablecimiento. La exportación respeta las columnas visibles y su
  orden.
- El PDF compilado adopta el nombre solicitado en el issue: código de proyecto,
  convenio, número de rendición y mes/año abreviado en español; por ejemplo,
  `APAR043-P01-RENDICION_1-JUL2026.pdf`. Los componentes variables se normalizan
  para evitar separadores de ruta u otros caracteres inseguros; los guiones
  medios separan los bloques y los separadores internos se convierten en guiones
  bajos. El nombre final no contiene espacios.
- Las pills de etapa se diferencian con una paleta pastel: Revisión Territorial
  en azul claro, Revisión de Auditoría en lavanda y Auditoría en durazno. Carga
  de documentación usa gris claro y Regularización amarillo crema. Los tonos
  tienen saturación media para destacarse sin perder el carácter pastel. Se
  conserva sin cambios el código semántico de estado: amarillo para en curso,
  verde para finalizado y rojo para correcciones.

## Validación de la reapertura

- Suite focalizada de Rendiciones y API PWA: `88 passed`.
- Suite completa del repositorio: `4068 passed`, `11 skipped`.
- `black`, `djlint`, `pylint`, chequeo Django y control de migraciones: exitosos.

## Correcciones del comentario del 24 de agosto

- La confirmación de reenvío lista solo solicitudes de documentos faltantes y
  versiones que continúan efectivamente a subsanar; una versión ya reemplazada
  no vuelve a aparecer por conservar su estado histórico.
- La progresividad y la prohibición de períodos repetidos se aplican a todo el
  proyecto, incluso cuando las rendiciones usan convenios diferentes. La PWA
  replica la validación antes de crear el registro offline.
- El PDF consolidado incluye exclusivamente las versiones vigentes con estado
  validado y excluye del exportable los documentos históricos subsanados.
- Se conserva la carga de documentos nuevos en categorías múltiples durante una
  subsanación sin exigir un documento observado para reemplazar.
- Las consultas PWA reconocen las rendiciones creadas desde un espacio para
  otro proyecto de la misma organización. Esto evita que el alta termine bien
  pero las cargas posteriores reciban `Rendición no encontrada`.

La PWA compiló correctamente con TypeScript y Vite. La suite focalizada de
servicios de rendiciones y API PWA finalizó con `71 passed`.
La regresión adicional de creación y carga multiproyecto finalizó correctamente
junto con los casos de scope y períodos (`3 passed`).
La suite completa posterior a las correcciones finalizó con `4096 passed` y
`11 skipped`.
