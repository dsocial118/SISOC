# Mobile rendición de cuentas: fase 1

Fecha: 2026-03-30

## Resumen

Se reemplazó el placeholder del módulo de Rendición de Cuentas en SISOC Mobile por una primera versión operativa con:

- listado de rendiciones,
- alta de datos generales,
- detalle inicial,
- carga de documentación categorizada,
- eliminación de archivos antes de presentar,
- envío a revisión con validación de obligatorios.

## Backend

- Se extendió `rendicioncuentasmensual.RendicionCuentaMensual` con:
  - `convenio`
  - `numero_rendicion`
  - `periodo_inicio`
  - `periodo_fin`
  - `estado`
- Se extendió `rendicioncuentasmensual.DocumentacionAdjunta` con:
  - `categoria`
  - `estado`
  - `observaciones`
- Se agregó la migración `0005_documentacionadjunta_categorias_estado.py`.
- Se mantiene la creación PWA de rendiciones en `POST /api/comedores/{id}/rendiciones/`.
- Se agregó carga documental categorizada en:
  - `POST /api/comedores/{id}/rendiciones/{rendicion_id}/documentacion/`
- Se agregó baja lógica de documentos en:
  - `POST /api/comedores/{id}/rendiciones/{rendicion_id}/documentacion/{documento_id}/eliminar/`
- Se mantuvo `POST /comprobantes/` como alias de compatibilidad para cargar en categoría `Comprobante/s`.
- `POST /presentar/` ahora valida documentación obligatoria antes de pasar a revisión.

## Mobile

- Nueva pantalla de listado de rendiciones.
- Nueva pantalla de alta de datos generales.
- Nueva pantalla de detalle con documentación agrupada por categoría.
- Cada categoría muestra si es obligatoria u opcional y si admite uno o varios archivos.
- Antes de presentar se permite adjuntar y eliminar documentos desde Mobile.
- La carga documental ofrece acciones separadas de `Sacar foto`, `Imagen de galeria` y `Subir archivo`, usando las capacidades disponibles del navegador/PWA.
- El acceso a `Rendición de Cuentas` se movió desde el footer del Hub a la barra inferior para usuarios organización.
- El header global y los encabezados internos de rendición dejaron de mostrar nombre de espacio para no reforzar una asociación incorrecta con un solo espacio.

## Supuestos de esta fase

- La rendición sigue anclada al espacio seleccionado porque el modelo actual no tiene entidad propia de `Proyecto`.
- Para aproximar el alcance por proyecto, el backend agrupa rendiciones por `codigo_de_proyecto` cuando el espacio lo tiene informado.
- El permiso específico de rendición no se activó todavía en Mobile porque el repo no expone un codename operativo claro para reutilizar sin inventarlo.
- Los modelos descargables, las observaciones por documento, la subsanación y el consolidado quedan para fases siguientes.
- En esta fase, `Convenio` se ingresa manualmente porque no existe aún un catálogo Mobile de convenios.
- Aunque el acceso ahora vive en la barra inferior, la navegación sigue resolviendo la rendición desde el contexto activo de espacio/proyecto de la fase 1.
- Supuesto aplicado sobre categorías: `Comprobante/s` y `Otros` aceptan múltiples archivos; el resto admite un único archivo activo.
- Supuesto aplicado sobre obligatoriedad: `Formulario II`, `Formulario III`, `Formulario V`, `Extracto Bancario` y `Comprobante/s` son obligatorios; `Formulario IV`, `Formulario VI`, `Planilla de Seguros` y `Otros` quedan optativos.

## Validación ejecutada

- `docker-compose exec django pytest tests/test_pwa_comedores_api.py -k rendicion`
- `docker-compose exec django python manage.py makemigrations --check`
- `npm run build` en `mobile/`

## Optimizacion 2026-03-30

- Se aliviano `GET /api/comedores/{id}/rendiciones/` para que no prefetchee `archivos_adjuntos` en el listado.
- La carga completa de documentos queda concentrada en detalle y en las acciones de adjuntar, eliminar y presentar.
- En Mobile se deduplican requests de listado en vuelo para evitar dobles llamadas equivalentes bajo `React.StrictMode` en desarrollo.

## Ajuste UX 2026-03-30

- En la carga documental se removio el campo manual `Nombre del archivo` para todas las categorias fijas.
- Ese campo queda disponible solo para la categoria `Documentacion Extra`.
- La categoria `Otros` pasa a mostrarse como `Documentacion Extra`.
- `Documentacion Extra` se carga de a un archivo por vez desde un boton `Añadir documentacion extra`; luego de adjuntar vuelve a quedar disponible el boton para agregar otro archivo extra.
- La carga documental acepta archivos de Office, PDF e imagen.
- Los botones de carga quedaron sin textos explicativos secundarios; se mantiene solo icono y titulo.

## Permisos 2026-03-30

- Se definio el permiso canonico `rendicioncuentasmensual.manage_mobile_rendicion` para habilitar el acceso a rendicion desde SISOC Mobile.
- Los endpoints mobile de rendicion ahora exigen dos condiciones:
  - ser representante activo del comedor,
  - y tener el permiso especifico de rendicion.
- Mobile persiste `permissions` desde `/api/users/me/` y usa ese dato para:
  - ocultar la opcion `Rendicion` del menu si el usuario no esta habilitado,
  - bloquear las rutas de rendicion aunque el usuario intente entrar por URL directa.
- La gestion del permiso queda del lado de SISOC Web, alineada con el requerimiento funcional.
- En el formulario de usuario de SISOC Web el permiso se administra con un check dedicado `Puede gestionar rendiciones mobile` dentro de la card `SISOC - Mobile`, visible solo cuando el usuario tiene acceso mobile.
