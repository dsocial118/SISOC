# Plan — Issue #1605 (comentario jcamiloparra, 2026-05-22)

Rama propuesta: `codex/issue-1605-resync-tipo-entidad`
Fecha: 2026-05-22
Estado: pendiente de aprobacion.

## Contexto

El comentario [#4519271427](https://github.com/dsocial118/SISOC/issues/1605#issuecomment-4519271427) identifica tres problemas vinculados entre el legajo de Organizacion y la Admision tecnica:

1. **Desincronizacion** entre `Admision.tipo_convenio` y `Organizacion.tipo_entidad` cuando este ultimo se modifica despues de iniciar la admision. La admision puede quedar "trabada" con documentacion incompatible.
2. **Bug**: al cambiar `tipo_entidad` en el legajo Organizacion, el sistema sigue exponiendo documentos adjuntos previos (de otra categoria), arrastrando estado obsoleto.
3. **Numero de GDE** vive hoy en `ArchivoOrganizacion`. La regla operativa es que el GDE debe ser propiedad de la Admision (puede repetirse el archivo de organizacion en varias admisiones, cada una con su GDE).

Las tres secciones se atacan **en orden** porque la solucion de la #2 deja en estado limpio el legajo organizacion, lo que simplifica el reset que pide la #1 (opcion "Actualizar desde Legajo"). La #3 es independiente de las anteriores pero comparte la vista `documento_row.html`.

## Hallazgos previos clave

- `Admision.tipo_convenio` → FK a `TipoConvenio` (admisiones/models/admisiones.py).
- `Organizacion.tipo_entidad` → FK a `TipoEntidad` (organizaciones/models.py).
- Mapa hardcodeado `CATEGORIA_ORGANIZACIONAL_POR_TIPO_CONVENIO` en [admisiones/services/admisiones_service/impl.py:89-93](admisiones/services/admisiones_service/impl.py) traduce `tipo_convenio_id` ↔ `DocumentacionOrganizacion.categoria`.
- Mapa por nombre `_categoria_documental_organizacion` en [organizaciones/views.py:117](organizaciones/views.py) traduce `tipo_entidad.nombre` ↔ `categoria` por palabras clave ("ecles", "base", "hecho").
- `AdmisionService._aplicar_cambio_convenio_y_reset_documentos` en [admisiones/services/admisiones_service/impl.py:987](admisiones/services/admisiones_service/impl.py) ya reusable.
- Modal previo de cambio de convenio en [admisiones/templates/admisiones/admisiones_tecnicos_form.html:546-588](admisiones/templates/admisiones/admisiones_tecnicos_form.html) sirve como referencia visual.
- Endpoint AJAX GDE Admision: `actualizar_numero_gde_archivo` ([admisiones/views/web_views.py:629](admisiones/views/web_views.py)) ya valida `estado == "Aceptado"`.
- Endpoint AJAX GDE Organizacion: `actualizar_gde_documento_organizacion` ([organizaciones/views.py:926](organizaciones/views.py)) NO valida estado.
- `OrganizacionUpdateView.form_valid` ([organizaciones/views.py:642-661](organizaciones/views.py)) hoy guarda sin reaccionar a cambios.
- Autocomplete GDE en informe tecnico: `_ultimo_numero_gde` ([admisiones/forms/admisiones_forms.py:15](admisiones/forms/admisiones_forms.py)).

## Diseno helper compartido

Se centraliza el mapeo `TipoEntidad → TipoConvenio` (hoy disperso entre el dict por id y el matching por nombre). Nuevo helper:

- `admisiones/services/tipo_convenio_resolver.py` (modulo nuevo, sin estado):
  - `categoria_para_tipo_entidad(tipo_entidad) -> str` (reusa la heuristica de `_categoria_documental_organizacion`).
  - `tipo_convenio_para_tipo_entidad(tipo_entidad) -> TipoConvenio | None` (mapea categoria → `TipoConvenio` via `CATEGORIA_ORGANIZACIONAL_POR_TIPO_CONVENIO` invertido).
  - `admision_desincronizada(admision) -> bool`.

`organizaciones/views.py` y `admisiones/services/admisiones_service/impl.py` deben pasar a importarlo en lugar de duplicar logica.

---

## Seccion 1 — Resync Admision ↔ Organizacion (1.1 a 1.5)

### Modelo

Agregar a `Admision`:

- `tipo_entidad_origen` → FK `TipoEntidad`, `on_delete=SET_NULL`, nullable. Snapshot del `tipo_entidad` de la organizacion en el momento en que la admision quedo en sync (creacion, "Actualizar desde Legajo", o "Continuar operando").

Migracion separada (no destructiva): backfill = `comedor.organizacion.tipo_entidad` al momento de la migracion para todas las admisiones existentes.

### Servicio

Agregar a `AdmisionService` (admisiones/services/admisiones_service/impl.py):

- `esta_desincronizada(admision)`:
  - `org_te = admision.comedor.organizacion.tipo_entidad`
  - Devuelve `True` si `admision.tipo_entidad_origen_id != org_te.id` (y ambos no nulos).
- `resync_admision_desde_organizacion(admision)`:
  - Resuelve `nuevo_convenio = tipo_convenio_para_tipo_entidad(org.tipo_entidad)`.
  - Reusa `_aplicar_cambio_convenio_y_reset_documentos` (ya borra `ArchivoAdmision` y resetea estado).
  - `admision.tipo_entidad_origen = org.tipo_entidad; admision.save(...)`.
  - Registrar audit log.
- `aceptar_desincronizacion_admision(admision)`:
  - Solo `admision.tipo_entidad_origen = org.tipo_entidad; admision.save(...)`. No toca documentos ni estado.

### URL + view

Nueva URL en `admisiones/urls/web_urls.py`:

```
path("admisiones/<int:pk>/resync-convenio/", resync_convenio_admision, name="admision_resync_convenio")
```

Vista `resync_convenio_admision` (admisiones/views/web_views.py): `@require_POST`, recibe `accion = "actualizar" | "continuar"`, delega al service, responde JSON `{success, redirect}` o `{success, mensaje}`.

### Template

En [admisiones/templates/admisiones/admisiones_tecnicos_form.html](admisiones/templates/admisiones/admisiones_tecnicos_form.html):

1. **Banner** sobre el cuerpo del formulario, condicional a `admision_desincronizada` (booleano que pasa la view):
   - `alert alert-warning` no dismissable.
   - Texto: "El tipo de convenio fue actualizado desde el Legajo de la Organizacion. Para continuar con la admision debe seleccionar una de las siguientes opciones".
   - `<select id="accionResyncConvenio" required>` con 2 `<option>` (placeholder + 2 valores).
   - Boton "Aplicar" deshabilitado hasta que se elija.

2. **Modal secundario** `modalConfirmarResync` que al confirmar emite POST al endpoint nuevo. El mensaje cambia segun la opcion:
   - actualizar: "La informacion de la Admision se actualizara desde el Legajo de la Organizacion y se perdera el progreso realizado. Esta seguro de continuar?"
   - continuar: "Continuara gestionando la Admision con la informacion ya procesada, sin las ultimas actualizaciones realizadas al Legajo de la Organizacion correpondiente. Esta seguro de continuar?"

3. **Bloqueo de UI**: mientras `admision_desincronizada == True`, agregar `pointer-events:none; opacity:.5` al resto del formulario via clase `.admision-bloqueada-por-resync`. Asi se obliga al usuario a elegir (1.2).

### JS

Nuevo archivo `static/custom/js/admisionResyncConvenio.js`:
- Listener del select → habilita boton aplicar.
- Click aplicar → abre `modalConfirmarResync` con texto correspondiente.
- Confirm → fetch al endpoint, recarga la pagina al exito (la admision quedara en sync, banner desaparece).

### Sincronizacion

- Pasar a la view (`AdmisionTecnicoEditView.get_context_data`) el flag `admision_desincronizada = AdmisionService.esta_desincronizada(self.object)`.
- En el momento de **crear** una admision (donde sea que se persista por primera vez) setear `tipo_entidad_origen = comedor.organizacion.tipo_entidad`. Buscar el create handler en [admisiones/services/admisiones_service/impl.py](admisiones/services/admisiones_service/impl.py) (`procesar_post_caratulacion` y el flow de creacion).

---

## Seccion 2 — Reset documentacion al cambiar tipo_entidad (2.1, 2.2)

### Backend

Modificar `OrganizacionUpdateView` ([organizaciones/views.py:642](organizaciones/views.py)):

```python
def form_valid(self, form):
    anterior = Organizacion.objects.only("tipo_entidad_id").get(pk=self.object.pk)
    tipo_anterior_id = anterior.tipo_entidad_id
    self.object = form.save()
    if tipo_anterior_id != self.object.tipo_entidad_id:
        ArchivoOrganizacion.objects.filter(organizacion=self.object).delete()
    return HttpResponseRedirect(self.get_success_url())
```

Decisiones:
- Borrar TODOS los `ArchivoOrganizacion` de la org (no solo los de la categoria), para cubrir 2.2 (volver a un tipo previo deja igualmente lista vacia).
- Borrado fisico (no soft-delete) porque la documentacion asociada cambia de categoria — mantenerla generaria registros huerfanos.
- Si la admision ya consumio esos archivos, la Seccion 1 cubrira la desincronizacion en la admision.

### UI confirmacion

Agregar modal de confirmacion en [organizaciones/templates/organizacion_form.html](organizaciones/templates/organizacion_form.html) cuando el `<select>` `tipo_entidad` cambia respecto al valor original:

- Mensaje: "Cambiar el Tipo de Entidad reiniciara la documentacion cargada para esta Organizacion. Esta seguro?"
- Si cancela → revertir el select al valor original.
- Si confirma → continuar normal con el submit.

Esto satisface la mencion del primer comentario (1.3 del comentario original): "Asi como actualmente existe una advertencia que se visualiza cuando se modifica el tipo de convenio desde la admision, debe implementarse un cartel de advertencia cuando se modifique el `Tipo de Entidad` desde el legajo organizacion".

### Cleanup

Eliminar (o ignorar) el fetch JS de `tipo_entidad` que solo refresca el `subtipo_entidad` (organizacionesform.js:65-102) si entra en conflicto con el nuevo modal. Mantener el refresco pero condicionarlo a la confirmacion.

---

## Seccion 3 — Numero GDE propiedad de la Admision (3.1 a 3.4)

### Modelo nuevo

`admisiones/models/numero_gde_organizacion.py`:

```python
class NumeroGdeOrganizacion(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.CASCADE, related_name="numeros_gde_organizacion")
    archivo_organizacion = models.ForeignKey("organizaciones.ArchivoOrganizacion", on_delete=models.CASCADE, related_name="numeros_gde_por_admision")
    numero_gde = models.CharField(max_length=50, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["admision", "archivo_organizacion"], name="unq_gde_admision_archivoorg")]
```

Migracion incluye **backfill** opcional: si `ArchivoOrganizacion.numero_gde` esta seteado y existe admision asociada, crear el registro `NumeroGdeOrganizacion` correspondiente (solo si hay forma univoca; si la org tiene varias admisiones, no copiar para evitar ambiguedad — dejar en blanco y registrar en el changelog).

### Cambios en serializacion

`AdmisionService._build_documentos_organizacionales_update_context` ([admisiones/services/admisiones_service/impl.py:335](admisiones/services/admisiones_service/impl.py)):
- Para cada `archivo_org`, buscar (o crear lazy) el `NumeroGdeOrganizacion` para la admision actual.
- En el dict serializado, exponer `numero_gde` desde ese registro (no desde `archivo_org.numero_gde`).
- Agregar key `numero_gde_record_id` para que el front sepa que endpoint llamar.

### Template

`admisiones/templates/admisiones/includes/documento_row.html`:
- Ajustar la celda `gde-{{ doc.id }}` ([linea 110](admisiones/templates/admisiones/includes/documento_row.html)) para:
  - Si `doc.es_documento_organizacion` y `doc.estado == "Aceptado"` → usar el endpoint nuevo (con `numero_gde_record_id`).
  - Si no → comportamiento actual (admision propia).
- El check `doc.estado == "Aceptado"` ya queda igual (3.4 ya cumplido para admision, lo extendemos a org-docs).

### Nuevo endpoint AJAX

`admisiones/urls/web_urls.py`:
```
path("ajax/actualizar-numero-gde-organizacion/", actualizar_numero_gde_organizacion_admision, name="actualizar_numero_gde_organizacion_admision")
```

Vista en [admisiones/views/web_views.py](admisiones/views/web_views.py): recibe `archivo_organizacion_id` + `admision_id` + `numero_gde`; valida que el `ArchivoOrganizacion.estado == "Aceptado"`; valida permisos (mismo `_puede_editar_numero_gde`); hace `update_or_create` del `NumeroGdeOrganizacion`.

### Quitar GDE editable del Legajo Organizacion

[organizaciones/templates/organizaciones/partials/documentacion_organizacion_row.html](organizaciones/templates/organizaciones/partials/documentacion_organizacion_row.html):
- Reemplazar el bloque editable de `numero_gde` por: solo lectura, leyenda informativa "El numero GDE se gestiona desde cada Admision".

Endpoint `organizacion_documento_gde` queda **deprecado**: cambiar a `@require_GET` con 410 Gone o eliminar la ruta + tests cercanos. Decision: eliminar para no dejar codigo muerto.

### Autocomplete informe tecnico

`_ultimo_numero_gde` en [admisiones/forms/admisiones_forms.py:15](admisiones/forms/admisiones_forms.py):
- Hoy solo busca en `ArchivoAdmision`. Extender para que tambien busque en `NumeroGdeOrganizacion` (por la misma admision, ordenado por modificado).
- Si la documentacion en cuestion es de organizacion, priorizar el valor org-side; sino, mantener el comportamiento actual.

---

## Orden de implementacion

1. **Helper compartido** `tipo_convenio_resolver` (sin breaking changes).
2. **Seccion 2** primero — es la base limpia y desbloquea testing manual de la #1.
3. **Seccion 1** — depende de #2 para que la opcion "Actualizar desde Legajo" deje un legajo coherente.
4. **Seccion 3** — independiente, pero comparte template `documento_row.html` con #1; mejor despues para no entrelazar conflictos de merge.

Cada seccion = 1 commit revisable independiente. Si el alcance crece, separar por modelo/migracion + UI.

## Archivos clave

| Archivo | Cambio |
|---|---|
| `admisiones/models/admisiones.py` | + campo `tipo_entidad_origen` |
| `admisiones/models/numero_gde_organizacion.py` | nuevo modelo |
| `admisiones/migrations/00XX_*` | dos migraciones nuevas (campo + modelo) con backfill |
| `admisiones/services/tipo_convenio_resolver.py` | nuevo, centraliza mapeo |
| `admisiones/services/admisiones_service/impl.py` | + `esta_desincronizada`, `resync_admision_desde_organizacion`, `aceptar_desincronizacion_admision`, ajuste `_build_documentos_organizacionales_update_context` |
| `admisiones/forms/admisiones_forms.py` | extender `_ultimo_numero_gde` |
| `admisiones/views/web_views.py` | 2 endpoints nuevos |
| `admisiones/urls/web_urls.py` | 2 rutas nuevas; revisar contexto que pasa al template |
| `admisiones/templates/admisiones/admisiones_tecnicos_form.html` | banner + modal de resync |
| `admisiones/templates/admisiones/includes/documento_row.html` | GDE org-doc editable |
| `static/custom/js/admisionResyncConvenio.js` | nuevo |
| `organizaciones/views.py` | `OrganizacionUpdateView.form_valid` reset + remover `actualizar_gde_documento_organizacion` |
| `organizaciones/urls.py` | remover ruta `organizacion_documento_gde` |
| `organizaciones/templates/organizacion_form.html` | modal confirmacion cambio tipo_entidad |
| `organizaciones/templates/organizaciones/partials/documentacion_organizacion_row.html` | GDE solo lectura |

## Validacion

Manual (post-cambio):
1. **Seccion 2**: ir a Organizacion → cambiar `tipo_entidad` → confirmar advertencia → verificar que el listado de documentos queda vacio. Volver al tipo anterior → sigue vacio.
2. **Seccion 1 escenario A**: admision en `Documentacion en Proceso` → cambiar `tipo_entidad` de la org → volver a la admision → ver banner. Elegir "Actualizar" → confirmar → admision queda reseteada, en estado inicial, con docs de la nueva categoria.
3. **Seccion 1 escenario B**: idem, pero elegir "Continuar" → banner desaparece, admision sigue como estaba.
4. **Seccion 3**: admision con doc de organizacion en estado `Aceptado` → editar GDE desde la admision → guardar → recargar → persiste. Verificar que la misma org doc en otra admision puede tener otro GDE. Verificar que el form de informe tecnico autocompleta.

Automatizada:
- `pytest admisiones/tests/test_tipo_convenio_resolver.py` (nuevo)
- `pytest admisiones/tests/test_resync.py` (nuevo)
- `pytest organizaciones/tests/test_update_view.py` (extender)
- `pytest admisiones/tests/test_numero_gde_organizacion.py` (nuevo)
- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 validate`

## Registro

Al cerrar la PR:
- `docs/registro/cambios/2026-05-22-issue-1605-resync-tipo-entidad.md`
- `docs/registro/decisiones/2026-05-22-numero-gde-propiedad-admision.md`

## Supuestos

1. La heuristica por nombre actual de `_categoria_documental_organizacion` es la fuente de verdad oficial. Si el equipo quiere migrar a un mapeo explicito (FK directa entre `TipoEntidad` ↔ `TipoConvenio`), se hace en una decision aparte; este plan lo encapsula en un helper para que el cambio futuro sea de un solo lugar.
2. El reset destructivo de `ArchivoOrganizacion` (Seccion 2) es aceptable porque la documentacion previa pierde validez al cambiar categoria. Si se requiere preservar historico, habria que mover a soft-delete; queda fuera de este plan.
3. La accion "Continuar operando con la Admision actual" deja el snapshot actualizado, lo que significa que un cambio posterior de `tipo_entidad` volvera a disparar el banner. Esto matchea la lectura literal del spec (cada cambio nuevo debe pedir decision).
