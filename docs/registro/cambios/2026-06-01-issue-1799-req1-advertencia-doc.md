# 2026-06-01 — Issue #1799 (Req 1): advertencia ante cambios en la documentacion del legajo

Rama: `claude/issue-1799-req1-advertencia-doc` (apilada sobre Req 3)
Plan: [docs/plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md](../../plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md)

## Resumen

Generaliza el mecanismo de advertencia del #1605 (que solo cubria el cambio de
Tipo de Entidad) a **cualquier cambio en la documentacion del legajo**, listando
los documentos modificados, con las 2 opciones (Actualizar / Continuar) y la
confirmacion de 2 pasos ya existentes.

## Cambios

- Modelo `AdmisionDocOrgSnapshot(admision, slot_key, etiqueta, token, synced_at)`
  (unique por `admision`+`slot_key`). Migracion
  [0063_admisiondocorgsnapshot_and_more.py](../../../admisiones/migrations/0063_admisiondocorgsnapshot_and_more.py).
  Indexa por slot logico: `doc:{id}` (catalogo) / `custom:{id}` (personalizado).
- Servicio (`AdmisionService`):
  - `_org_archivos_relevantes` / `_tokens_org_actuales`: estado actual del legajo
    que alimenta a la admision (catalogo + personalizados). El `token` captura
    archivo, estado y vencimiento; **excluye numero_gde** (se replica aparte, Req 3).
  - `refrescar_snapshot_documentacion_organizacional`: upsert + limpieza de slots.
  - `admision_documentacion_desactualizada -> (bool, [labels])`: diff snapshot vs
    actual; lazy-init en sync para admisiones sin snapshot (req 1.6); detecta
    add/modify/remove e incluye `Pendiente -> Aceptado` (req 1.7).
  - Refresco del snapshot en `create_admision`, `resync_admision_desde_organizacion`
    (Actualizar) y `aceptar_desincronizacion_admision` (Continuar).
  - `congelar_documentacion_organizacional` ahora **materializa tambien los
    personalizados** (completa la materializacion diferida del Req 4), usando la
    FK de procedencia (Fase 0) para deduplicar.
- Contexto: `_build_response_update_context` expone `documentacion_desactualizada`,
  `documentos_org_modificados` y `mostrar_modal_resync_org`.
- Template `admisiones_tecnicos_form.html`: el modal bloqueante ahora dispara por
  cambio de convenio **o** de documentacion, con encabezado segun motivo y el
  listado de documentos modificados. Reusa el mismo `<select>`, endpoint
  (`resync_convenio_admision`) y JS (`admisionResyncConvenio.js`); los textos de
  confirmacion (paso 2) ya coincidian con el req 1.3.

## Flujo

- "Actualizar Información desde Legajo Organización": reusa
  `resync_admision_desde_organizacion` (borra ArchivoAdmision, re-materializa desde
  el legajo y refresca el snapshot) — req 1.4 (se pierde el progreso).
- "Continuar operando con la Admisión actual": `aceptar_desincronizacion_admision`
  refresca el snapshot sin tocar documentos — la advertencia desaparece hasta el
  proximo cambio.

## Validacion

Entorno local Windows (venv Django 4.2.27, sqlite; Docker apagado):

- `pytest admisiones/ organizaciones/` → 79 passed (incluye
  `test_documentacion_desactualizada.py`: lazy-init, cambio de estado
  Pendiente->Aceptado, vencimiento, alta de adicional, y silenciado por "Continuar").
- `manage.py makemigrations --check --dry-run admisiones organizaciones` → sin cambios.
- `manage.py migrate admisiones` (sqlite) → aplica 0063 OK.
- `black` + `djlint --check` sobre lo tocado → limpio.

## Notas

- El `token` excluye `numero_gde` para no disparar la advertencia ante cambios de
  GDE (que se replican automaticamente, Req 3).
- Eficiencia: el diff se evalua por render de la admision; usa los helpers de
  vigencia existentes. Si se observa costo, cachear por request.
