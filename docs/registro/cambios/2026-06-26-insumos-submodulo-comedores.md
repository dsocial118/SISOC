# Submódulo "Insumos" para comedores (repositorio de documentos)

## Fecha
2026-06-26

## Objetivo
Reemplazar la carpeta de Google Drive del programa de comedores por un submódulo
interno que permita almacenar, organizar por categorías y descargar documentos,
con dos roles diferenciados: gestión (CRUD completo) y consulta (ver + descargar).

## Alcance
App nueva `insumos`: `models.py`, `forms.py`, `services.py`, `views.py`,
`urls.py`, `admin.py`, `validators.py`, plantillas en `insumos/templates/insumos/`
y `insumos/tests/`. Cableado en `config/settings.py` (INSTALLED_APPS),
`config/urls.py`, `templates/includes/sidebar/opciones.html` y grupos bootstrap en
`users/bootstrap/groups_seed.py`.

## Cambios realizados
- **Modelos**: `InsumoCategoria` (FK a `core.Programa`, nombre, descripción,
  orden, activo; único por programa+nombre) e `Insumo` (FK a programa, FK opcional
  a categoría con `SET_NULL`, título, descripción, `FileField` validado, `activo`,
  timestamps y `usuario_creacion`/`usuario_actualizacion`). FK a programa con
  `PROTECT` para no perder documentos al borrar un programa.
- **Permisos (modelo IAM por permisos Django)**: se usan los permisos de modelo
  `insumos.view/add/change/delete_insumo` e `..._insumocategoria`. No se crean
  `auth.role_*` nuevos.
- **Grupos bootstrap**: `Comedor Insumos Gestión` (8 permisos: CRUD de ambos
  modelos) y `Comedor Insumos Consulta` (solo `view_insumo` + `view_insumocategoria`).
  Los 8 permisos también se sumaron al grupo `Admin`.
- **Descarga protegida (seguridad)**: el archivo NO se sirve por su URL pública de
  MEDIA. La vista `InsumoDescargarView` exige `insumos.view_insumo` (a nivel URL) y
  entrega el archivo vía `FileResponse(as_attachment=True)`. Funciona aunque el
  insumo esté `activo=False`, según lo pedido.
- **UI**: ítem "Insumos" dentro de "Configuración de Comedores" en
  `opciones.html`, visible solo con `insumos.view_insumo`. Botones Agregar/Editar/
  Eliminar y la gestión de categorías se muestran solo con permiso de gestión.
  Listado con filtro por categoría (incluye "Sin categoría") y búsqueda por texto.
- **Validación de archivos**: PDF, imágenes (JPG/PNG), Word, Excel y CSV; máx 10 MB
  (extensión + tamaño + content-type), siguiendo el patrón de `dispositivos`.

## Riesgo / Impacto
Feature nueva y aislada; no toca datos ni flujos existentes. Sin integraciones
externas (GESTIONAR/RENAPER no intervienen).

## Acción requerida antes de desplegar
1. `python manage.py migrate` (migración `insumos.0001_initial`).
2. `python manage.py sync_group_permissions_from_registry` para materializar los
   nuevos grupos `Comedor Insumos Gestión` / `Comedor Insumos Consulta` y asignar
   sus permisos (incluye refuerzo del grupo `Admin`).
3. Asignar los grupos a los usuarios correspondientes.

## Rollback
Quitar `"insumos"` de `INSTALLED_APPS`, el `include("insumos.urls")`, el ítem del
sidebar y los grupos del seed; revertir la migración (`migrate insumos zero`). La
app es autocontenida, por lo que no deja dependencias en otras apps.

## Tests
`insumos/tests/test_insumos_permisos.py` (9 casos): visibilidad por permiso,
403 sin permiso, descarga por rol consulta, descarga con insumo inactivo, CRUD de
gestión y validación de categoría inconsistente entre programas.
