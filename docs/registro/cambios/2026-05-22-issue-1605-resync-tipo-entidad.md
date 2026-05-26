# 2026-05-22 — Issue #1605: resync tipo_entidad ↔ admision, reset documental y GDE por admision

Rama: `codex/issue-1605-resync-tipo-entidad`
Plan: [docs/plans/2026-05-22-issue-1605-jcamiloparra-design.md](../../plans/2026-05-22-issue-1605-jcamiloparra-design.md)

## Resumen

Implementa los tres requerimientos del comentario [#4519271427](https://github.com/dsocial118/SISOC/issues/1605#issuecomment-4519271427) reportado por jcamiloparra:

1. **Seccion 1** — advertencia + opciones cuando el `Tipo de Entidad` de la Organizacion cambia despues de creada la Admision.
2. **Seccion 2** — al modificar `Tipo de Entidad` desde el Legajo de la Organizacion, la documentacion del legajo se reinicia (sin adjuntos).
3. **Seccion 3** — el `Numero de GDE` pasa a ser propiedad de la Admision incluso para los documentos administrados desde la Organizacion (modelo `NumeroGdeOrganizacion`).

## Modelos / migraciones

- `Admision.tipo_entidad_origen` (FK `organizaciones.TipoEntidad`, nullable). Snapshot del `tipo_entidad` con el que la admision quedo sincronizada (creacion / resync / aceptacion). Migracion: [0059_admision_tipo_entidad_origen.py](../../../admisiones/migrations/0059_admision_tipo_entidad_origen.py) (incluye backfill).
- `NumeroGdeOrganizacion(admision, archivo_organizacion, numero_gde)` con unique_together. Reemplaza el uso editable de `ArchivoOrganizacion.numero_gde` (el campo queda en el modelo por compatibilidad historica). Migracion: [0060_numero_gde_organizacion.py](../../../admisiones/migrations/0060_numero_gde_organizacion.py) (incluye backfill conservador: solo copia GDE org-side si existe exactamente una admision asociada).

## Servicios

- Nuevo helper compartido: [`admisiones/services/tipo_convenio_resolver.py`](../../../admisiones/services/tipo_convenio_resolver.py). Centraliza el mapeo `tipo_entidad -> categoria documental -> TipoConvenio` para evitar drift entre `organizaciones/views.py` y `admisiones_service`.
- `AdmisionService.admision_desincronizada(admision)` compara el snapshot `tipo_entidad_origen` con el `tipo_entidad` actual de la organizacion.
- `AdmisionService.resync_admision_desde_organizacion(admision)` reusa `_aplicar_cambio_convenio_y_reset_documentos` (borra `ArchivoAdmision`, resetea estado, ajusta `tipo_convenio`) y actualiza el snapshot.
- `AdmisionService.aceptar_desincronizacion_admision(admision)` solo actualiza el snapshot al `tipo_entidad` actual para silenciar la advertencia hasta el proximo cambio.
- `AdmisionService.actualizar_numero_gde_organizacion_ajax(request)` valida `ArchivoOrganizacion.estado == "Aceptado"`, permisos dupla/superuser, restriccion documental por informe tecnico, y persiste el GDE en `NumeroGdeOrganizacion` (`update_or_create`).
- `AdmisionService._build_documentos_organizacionales_update_context` y `_serializar_documentacion_organizacion` ahora exponen `archivo_organizacion_id` + `numero_gde` desde `NumeroGdeOrganizacion` (no desde `ArchivoOrganizacion.numero_gde`).
- `admisiones/forms/admisiones_forms.py::_ultimo_numero_gde` extiende la busqueda a `NumeroGdeOrganizacion` cuando no hay valor en `ArchivoAdmision`.
- `AdmisionService.create_admision` setea `tipo_entidad_origen = comedor.organizacion.tipo_entidad` al crear la admision.

## Vistas / URLs

- Nuevas rutas en [`admisiones/urls/web_urls.py`](../../../admisiones/urls/web_urls.py):
  - `ajax/actualizar-numero-gde-organizacion/` → `actualizar_numero_gde_organizacion_admision` (POST, persiste `NumeroGdeOrganizacion`).
  - `admisiones/<int:admision_pk>/resync-convenio/` → `resync_convenio_admision` (POST con `accion="actualizar"|"continuar"`).
- `OrganizacionUpdateView.form_valid` (organizaciones/views.py) detecta cambio de `tipo_entidad` y borra todos los `ArchivoOrganizacion` de la organizacion (cubre 2.1 y 2.2).
- Removida la vista `actualizar_gde_documento_organizacion` y la ruta `organizacion_documento_gde` (no estaba referenciada por templates; reemplazada por el flujo admision-side).

## Templates / JS

- [`admisiones_tecnicos_form.html`](../../../admisiones/templates/admisiones/admisiones_tecnicos_form.html): banner de desincronizacion con `<select>` obligatorio (Actualizar / Continuar) + modal de confirmacion con textos exactos del spec. Configurable via `admision_desincronizada`, `tipo_entidad_actual_organizacion`, `tipo_entidad_origen_snapshot` que ahora pasa `_build_response_update_context`.
- [`documento_row.html`](../../../admisiones/templates/admisiones/includes/documento_row.html): para documentos de organizacion en estado Aceptado sin `ArchivoAdmision`, expone editor GDE con id `gde-org-{archivo_organizacion_id}` que llama al endpoint nuevo. Mantiene el comportamiento previo para `ArchivoAdmision`.
- Nuevo [`static/custom/js/admisionResyncConvenio.js`](../../../static/custom/js/admisionResyncConvenio.js): maneja el flujo banner → modal → POST.
- [`admisionesactualizarestado.js`](../../../static/custom/js/admisionesactualizarestado.js): nuevas funciones `activarEdicionGDEOrganizacion`, `guardarNumeroGDEOrganizacion`, etc., reutilizando el config `admisiones-tecnicos-config`.
- [`organizacion_form.html`](../../../organizaciones/templates/organizacion_form.html): la advertencia previa al cambiar `tipo_entidad` se reforzo (ahora explicita el reset de documentacion) y se agrego modal de confirmacion antes de enviar el form.

## Validacion

Corrida via Docker (`docker compose up -d` + `pytest`):

```
pytest admisiones organizaciones --tb=short -q
56 passed in 18.33s
```

Tests nuevos (17 casos, todos pasan):

- [admisiones/tests/test_resync_admision.py](../../../admisiones/tests/test_resync_admision.py) — `admision_desincronizada`, `resync_admision_desde_organizacion`, `aceptar_desincronizacion_admision`, mapeo de categorias.
- [admisiones/tests/test_numero_gde_organizacion.py](../../../admisiones/tests/test_numero_gde_organizacion.py) — flujo completo de `actualizar_numero_gde_organizacion_ajax`, unique constraint, GDE por admision.
- [organizaciones/test_update_view_tipo_entidad.py](../../../organizaciones/test_update_view_tipo_entidad.py) — reset de `ArchivoOrganizacion` al cambiar `tipo_entidad` (incluye caso "volver al tipo anterior").

Adicional:
- `python manage.py check` → 0 issues.
- `python manage.py makemigrations --check --dry-run` → No changes detected.

## Riesgos / supuestos

1. La heuristica de mapeo `tipo_entidad -> tipo_convenio` sigue siendo por nombre (`AdmisionService.resolver_tipo_convenio_desde_organizacion`). Si se renombra un `TipoEntidad` con palabras fuera del patron (`personeria`, `ecles`, `culto`, `base`, `hecho`), la admision podria no resincronizar. El helper nuevo encapsula esto para facilitar una migracion futura a una FK explicita.
2. El reset de `ArchivoOrganizacion` es destructivo (no soft-delete). Si se necesita preservar historico, hay que migrar el modelo a soft-delete (fuera de scope).
3. El campo `ArchivoOrganizacion.numero_gde` queda intacto en DB para no perder datos historicos. El flujo nuevo lo ignora; queda como candidato a remover en una migracion futura.
4. La opcion "Continuar operando con la Admision actual" actualiza el snapshot, por lo que un cambio posterior de `tipo_entidad` volvera a disparar el banner — lectura literal del spec.

## Como probar manualmente

1. **Seccion 2**: editar una Organizacion, cambiar `Tipo de Entidad`, confirmar el modal y verificar que el listado de documentos del legajo queda vacio (incluso si se vuelve al tipo anterior).
2. **Seccion 1A**: con una admision en `Documentacion en Proceso`, cambiar `tipo_entidad` desde la organizacion, volver a la admision, elegir "Actualizar Informacion desde Legajo Organizacion" → confirmar → admision queda en `convenio_seleccionado`, documentos eliminados, `tipo_convenio` recalculado.
3. **Seccion 1B**: misma situacion, elegir "Continuar operando" → confirmar → la admision sigue como estaba y el banner desaparece.
4. **Seccion 3**: con una admision que muestra un documento de Organizacion en estado `Aceptado`, editar el `Numero de GDE` desde la admision, recargar, confirmar persistencia. Replicar el escenario en una segunda admision con la misma org para verificar que cada una tiene su propio GDE.
