# Plan — Issue #1799: Documentacion asociada a la Organizacion ↔ Admisiones

Issue: [#1799](https://github.com/dsocial118/SISOC/issues/1799) (HOTFIX, autor jcamiloparra, asignado juanikitro)
Fecha: 2026-06-01
Estado: pendiente de aprobacion.
Ramas propuestas (1 por requerimiento, todas desde `origin/development`):
- `codex/issue-1799-doc-adicional-organizacion` (Req 4)
- `codex/issue-1799-acta-vuelve-admision` (Req 2)
- `codex/issue-1799-gde-origen-organizacion` (Req 3)
- `codex/issue-1799-advertencia-doc-desactualizada` (Req 1)

---

## 0. Resumen ejecutivo

El #1799 es un **follow-up del #1605** (ya mergeado, PRs #1763-#1767). El #1605 dejo implementado el andamiaje de "advertencia + 2 opciones + confirmacion" para cambios de **Tipo de Entidad**, y movio el **Numero de GDE** a ser propiedad de la Admision (`NumeroGdeOrganizacion`). El #1799 pide:

1. **Generalizar** esa advertencia a **cualquier cambio de documentacion** del legajo (no solo tipo de entidad), listando los documentos modificados.
2. **Devolver** el "Acta de solicitud de subsidio" del legajo de Organizacion a las Admisiones.
3. **Revertir** la direccion del GDE: editarlo desde la Organizacion y replicarlo a las admisiones.
4. Agregar **Documentacion Adicional** (documentos personalizados) al legajo de Organizacion, como ya existe en Admisiones.

### Decisiones de producto confirmadas (2026-06-01)

- **GDE (Req 3): "Org unica fuente"**. El GDE se edita solo en el legajo (cuando el documento esta `Aceptado`), se replica a TODAS las admisiones relacionadas, se deshabilita la edicion desde la admision para documentos de origen organizacional y se migran los `NumeroGdeOrganizacion` existentes. Lectura literal del #1799 y consistente con el flujo unidireccional `Legajo Organizacion → Admision` (req 1.5).
- **Acta (Req 2): "Solo juridica (igual que hoy)"**. Se quita del catalogo de Organizacion (`personeria_juridica`) y queda como documento de Admision unicamente para convenio 3 (personeria juridica), sin ampliar alcance a base/eclesiastica.

---

## 1. Hallazgos clave del codigo actual (con file:line)

### Modelos
- `organizaciones.ArchivoOrganizacion` ([organizaciones/models.py:188](../../organizaciones/models.py)): FK `documentacion` es **obligatoria** y `on_delete=PROTECT` (linea 206-210). Tiene `numero_gde` (214-219) y `estado` (212). NO tiene `nombre_personalizado`.
- `organizaciones.DocumentacionOrganizacion` ([organizaciones/models.py:163](../../organizaciones/models.py)): catalogo fijo con `categoria` (164-172).
- `admisiones.ArchivoAdmision` ([admisiones/models/admisiones.py:300](../../admisiones/models/admisiones.py)): `documentacion` nullable (302-304), `nombre_personalizado` (305-307), `numero_gde` (327-333), propiedad `es_personalizado` (356-358). **No tiene FK de procedencia hacia `ArchivoOrganizacion`.**
- `admisiones.Admision.tipo_entidad_origen` ([admisiones/models/admisiones.py:122](../../admisiones/models/admisiones.py)): snapshot escalar del tipo de entidad.
- `admisiones.NumeroGdeOrganizacion` ([admisiones/models/admisiones.py:1196](../../admisiones/models/admisiones.py)): GDE por (admision, archivo_organizacion). **A deprecar.**

### Servicio (`admisiones/services/admisiones_service/impl.py`)
- `CATEGORIA_ORGANIZACIONAL_POR_TIPO_CONVENIO` (96-100): `1→base, 2→eclesiastica, 3→personeria`.
- `ALIAS_DOCUMENTACION_ORGANIZACIONAL` (101+): mapea nombres org↔admision. El acta esta mapeada en `personeria` (`"acta de solicitud de subsidio" → "acta de solicitud de subsidio al programa"`, linea 111).
- `congelar_documentacion_organizacional()` (2960): **copia** (materializa) cada `ArchivoOrganizacion` vigente de la categoria a un `ArchivoAdmision` propio. Solo itera el catalogo `DocumentacionOrganizacion` (no copia personalizados).
- `_crear_archivo_admision_desde_archivo_organizacion()` (317-341) y `_resolver_numero_gde_para_clonado()` (344-361).
- `_build_documentos_organizacionales_update_context()` (394-480), `_serializar_documentacion_organizacion()` (288-314), `_serialize_documentacion()` (364-391): serializan con flags `es_documento_organizacion` / `origen` y `archivo_organizacion_id`.
- `admision_desincronizada()` (1121-1138), `resync_admision_desde_organizacion()` (1141-1173), `aceptar_desincronizacion_admision()` (1176-1194), `_asegurar_snapshot_tipo_entidad()` (1104-1118), `_aplicar_cambio_convenio_y_reset_documentos()` (~1096).
- `create_admision()` (1974-2018) llama a `congelar_documentacion_organizacional` (2010).
- GDE admision-side: `actualizar_numero_gde_ajax()` (2160) y `actualizar_numero_gde_organizacion_ajax()` (2301). Permisos: `_puede_editar_numero_gde()` (2066).
- Documento personalizado admision: `crear_documento_personalizado()` (1360-1435), `serialize_documento_personalizado()` (559-580).
- `_build_response_update_context()` (858-904): expone `admision_desincronizada`, `tipo_entidad_actual_organizacion`, `tipo_entidad_origen_snapshot`.

### Vistas / URLs
- `admisiones/views/web_views.py`: `actualizar_numero_gde_archivo` (631), `actualizar_numero_gde_organizacion_admision` (649), `resync_convenio_admision` (667-695), `crear_documento_personalizado` (736-760).
- `admisiones/urls/web_urls.py`: `documento_personalizado_crear` (71-73), `admision_resync_convenio` (134-138), rutas GDE.
- `organizaciones/views.py`: `OrganizacionUpdateView.form_valid` (656-703) materializa+resetea al cambiar tipo_entidad; `subir_documento_organizacion` (839-912; **limpia numero_gde=None al re-subir**, linea 877; reemplazo de doc Aceptado crea fila nueva, 894-902); `actualizar_estado_documento_organizacion` (917-965); `actualizar_vencimiento_documento_organizacion` (970-1006); `OrganizacionDetailView` (706-810) arma filas iterando el catalogo (146-171).
- `organizaciones/urls.py` (76-101): subir / estado / vencimiento / historial. **No hay endpoint GDE org-side** (el #1605 lo removio).

### Templates / JS
- `admisiones/templates/admisiones/admisiones_tecnicos_form.html`: modal bloqueante de resync (41-103), seccion "Documentacion adicional" (504-542).
- `admisiones/templates/admisiones/includes/documento_row.html`: GDE admision (117-160) y GDE org-doc (`gde-org-*`, 161-203).
- `organizaciones/templates/organizaciones/partials/documentacion_organizacion_row.html` (1-142): columnas Nombre/Estado/Archivo/Vencimiento. **Sin columna GDE, sin personalizados.**
- `static/custom/js/admisionResyncConvenio.js`, `static/custom/js/admisionesactualizarestado.js` (GDE), `static/custom/js/admisionestecnico.js` (doc personalizado, 19-114), `static/custom/js/organizacionesDocumentos.js`.

---

## 2. Decisiones de diseno transversales (propuestas por IA, con fundamento)

### D1 — FK de procedencia `ArchivoAdmision.archivo_organizacion_origen` (nullable)
Hoy la relacion org-doc → admision-doc se resuelve por heuristica de nombre (alias). Para hacer **exacta** tanto la replicacion de GDE (Req 3) como el diff de cambios (Req 1), se agrega una FK nullable de procedencia que se setea en `congelar_documentacion_organizacional`. Es aditiva y no destructiva. Backfill best-effort por alias para registros existentes.

### D2 — Snapshot documental por admision (Req 1) indexado por *slot logico*
El reemplazo de un doc `Aceptado` crea una **fila nueva** de `ArchivoOrganizacion` (id nuevo). Por eso el snapshot NO puede indexarse por `archivo_organizacion_id`. Se indexa por **slot logico** = `DocumentacionOrganizacion` (catalogo) para docs de catalogo, y por `ArchivoOrganizacion.id` para personalizados (no tienen slot de catalogo). El snapshot guarda un **token de version** que captura lo que cuenta como "modificacion".

`token = f"{archivo_org_id}|{estado}|{archivo_name}|{fecha_vencimiento}"`

- Captura: reemplazo de archivo, cambio de estado (cubre 1.7 `Pendiente→Aceptado`), cambio de vencimiento (el caso motivador del issue), y add/remove (por presencia/ausencia de slot).
- **Excluye** `numero_gde` (se replica automaticamente por Req 3, no debe disparar la advertencia) y `observaciones` (interno).

### D3 — Unificar el motivo de desincronizacion
El modal del #1605 ya existe; se generaliza para soportar 2 causas: cambio de **tipo de convenio** (texto actual) y cambio de **documentacion** (texto del req 1, con listado de labels). Misma estructura de 2 pasos, mismo endpoint, distinto encabezado y cuerpo segun `desync_motivo ∈ {tipo_convenio, documentacion, ambos}`.

### D4 — Locus de edicion del GDE segun origen del documento
- Documentos **de origen organizacional** (materializados o en vivo): GDE editable **solo** en el legajo (Req 3). En la admision se muestra **solo lectura**.
- Documentos **nativos de la admision** (personalizados y el Acta tras Req 2): mantienen el GDE editable admision-side via `actualizar_numero_gde_archivo` (sin cambios).
- La distincion se hace por `archivo_organizacion_origen` (D1): si no es nulo → org-side.

### D5 — Deprecacion no destructiva de `NumeroGdeOrganizacion`
En un HOTFIX no borramos datos. Se deja de **escribir** en `NumeroGdeOrganizacion`, se backfillea su valor a `ArchivoOrganizacion.numero_gde` (resolviendo conflictos por "mas reciente") y se remueve la UI/endpoint admision-side para org-docs. El modelo y la tabla quedan para historico; su remocion fisica se evalua en una migracion posterior.

---

## 3. Diseno por requerimiento

> Orden de implementacion: **Fase 0 → Req 4 → Req 2 → Req 3 → Req 1** (ver §4). Cada fase = 1 PR revisable a `development`.

### Fase 0 — Fundacional (helper + procedencia)
**Objetivo:** dejar la base que consumen Req 1 y Req 3, sin cambios de comportamiento visibles.

- **Modelo/migracion:** agregar `ArchivoAdmision.archivo_organizacion_origen` (FK `organizaciones.ArchivoOrganizacion`, `on_delete=SET_NULL`, null=True, blank=True, `related_name="archivos_admision_materializados"`). Migracion con **backfill best-effort**: para cada `ArchivoAdmision` materializado, intentar resolver su `ArchivoOrganizacion` por alias/categoria y setear la FK. Loguear no resueltos.
- **Servicio:** `congelar_documentacion_organizacional` y `_crear_archivo_admision_desde_archivo_organizacion` setean `archivo_organizacion_origen`.
- **Helper:** mover/crear `admisiones/services/organizacion_sync.py` (o reusar `tipo_convenio_resolver.py`) con utilidades compartidas: resolucion de docs org vigentes por admision, normalizacion de nombres, y construccion del token (D2).
- **Tests:** materializacion setea la procedencia; backfill resuelve los casos por alias.

### Req 4 — Documentacion Adicional en el legajo de Organizacion
**Objetivo:** permitir documentos personalizados (nombre libre, opcionales, N) en el legajo, como en Admisiones.

- **Modelo/migracion (`organizaciones`):**
  - `ArchivoOrganizacion.documentacion` → `null=True, blank=True` y `on_delete=SET_NULL` (deja de ser obligatoria/PROTECT).
  - `ArchivoOrganizacion.nombre_personalizado` → `CharField(max_length=255, blank=True, null=True)`.
  - Propiedad `es_personalizado` = `documentacion_id is None` (espejo de `ArchivoAdmision`).
  - Migracion no destructiva (solo agrega columna nullable y afloja FK).
- **Vista/URL:** nuevo endpoint `organizacion_documento_personalizado_crear` (`organizaciones/urls.py`) → vista en `organizaciones/views.py` que valida permisos (mismo `_puede_enviar_documentacion_organizacion`), requiere `nombre` (obligatorio) y `archivo` (obligatorio), crea `ArchivoOrganizacion(documentacion=None, nombre_personalizado=..., estado=ESTADO_ADJUNTO)`. Espejo de `crear_documento_personalizado` admision.
- **Vista detalle:** extender el armado de filas en `OrganizacionDetailView` (146-171) para incluir tambien `ArchivoOrganizacion.objects.filter(organizacion=..., documentacion__isnull=True)` como filas adicionales.
- **Template:** seccion "Documentacion Adicional" en `organizacion_detail.html` (input nombre + adjuntar), y soportar `nombre_personalizado` en `documentacion_organizacion_row.html`. Boton eliminar para personalizados (espejo admision).
- **JS:** nuevo handler en `organizacionesDocumentos.js` (o archivo nuevo) para el alta del personalizado (FormData + XHR + insertar fila), espejo de `admisionestecnico.js:19-114`.
- **Interaccion con flujos existentes:** `congelar_documentacion_organizacional` debe **tambien** materializar personalizados (hoy solo itera el catalogo). Se agrega un segundo loop sobre los `ArchivoOrganizacion` personalizados vigentes → `ArchivoAdmision` con `documentacion=None`, `nombre_personalizado` y `archivo_organizacion_origen`.
- **Tests:** alta de personalizado en org; aparece en el detalle; se materializa a admisiones nuevas; valida nombre/archivo obligatorios y permisos.

### Req 2 — "Acta de solicitud de subsidio" vuelve a la Admision (solo juridica)
**Objetivo:** que el Acta deje de vivir en el catalogo de Organizacion y se gestione como documento nativo de Admision (convenio 3).

- **Datos/migracion (`organizaciones`):** data migration que:
  - Marca como soft-deleted (o elimina) los `ArchivoOrganizacion` cuyo `documentacion.nombre == "Acta de solicitud de subsidio al programa"` (categoria `personeria_juridica`).
  - Elimina la entrada de catalogo `DocumentacionOrganizacion` correspondiente (o la marca inactiva si se prefiere conservar historico — **decidir en PR**; por defecto eliminar la fila de catalogo dado que el #1605 ya hace resets destructivos del legajo).
  - Reverse no-op documentado.
- **Servicio:** quitar el alias del Acta del bloque `personeria` en `ALIAS_DOCUMENTACION_ORGANIZACIONAL` (linea 111) para que `congelar_documentacion_organizacional` deje de materializarla desde el legajo.
- **Catalogo admision:** el Acta ya existe como `Documentacion` pk 9 ("Acta de Solicitud de Subsidio", convenio 3) en [documentacion_tipoconvenio.json:100](../../admisiones/fixtures/documentacion_tipoconvenio.json). Verificar que este presente en la DB (es fixture); si falta, asegurarlo via migracion idempotente. **No** ampliar a convenios 1/2 (decision confirmada).
- **Comportamiento:** al ser doc nativo de admision, se adjunta/gestiona con la logica de `ArchivoAdmision` (subida, estado, GDE admision-side, rectificacion) — req 2.1 cumplido sin codigo nuevo, solo por el cambio de origen.
- **Compatibilidad:** admisiones existentes que ya materializaron el Acta conservan su `ArchivoAdmision` (queda como doc nativo). No se rompe nada.
- **Tests:** el Acta no aparece en el legajo org; aparece como doc de admision convenio 3; admisiones nuevas convenio 3 la piden admision-side; convenios 1/2 no la muestran.

### Req 3 — Numero de GDE: origen Organizacion, replica a Admisiones
**Objetivo:** revertir la direccion del GDE para documentos de origen organizacional.

- **Datos/migracion (`admisiones`):** data migration que backfillea `ArchivoOrganizacion.numero_gde` desde:
  1. `NumeroGdeOrganizacion` (por archivo_organizacion, valor mas reciente por `modificado`), y
  2. en su defecto, `ArchivoAdmision.numero_gde` de los materializados (via `archivo_organizacion_origen`).
  - **Resolucion de conflictos:** si distintas admisiones tienen GDE distinto para el mismo `ArchivoOrganizacion`, toma el mas reciente y **loguea** la divergencia (no se puede revertir perfectamente un modelo 1→N). Documentar en el changelog.
- **Org legajo (UI + endpoint):**
  - Nueva columna/celda GDE en `documentacion_organizacion_row.html`, **editable solo si `estado == "Aceptado"`** (req 3.2), con permisos del legajo (`_puede_enviar_documentacion_organizacion` / abogado-tecnico de la organizacion).
  - Nuevo endpoint `organizacion_documento_gde` (`@require_POST`) en `organizaciones/views.py` + ruta en `organizaciones/urls.py`. Valida estado Aceptado y permisos; setea `ArchivoOrganizacion.numero_gde`; **replica** (ver abajo).
  - JS en `organizacionesDocumentos.js`: edicion inline (espejo del patron admision-side GDE).
- **Replicacion org → admisiones (servicio):** al guardar el GDE de un `ArchivoOrganizacion`, replicar a TODAS las admisiones activas relacionadas (decision "replicar a todas"):
  - Para cada `ArchivoAdmision` con `archivo_organizacion_origen == <archivo_org>` (y/o resolucion por alias para no-materializados), setear `numero_gde`.
  - Para documentos de organizacion mostrados **en vivo** (no materializados), la serializacion lee `ArchivoOrganizacion.numero_gde` directamente (solo lectura).
  - Reusar `_limpiar_if_gde_admision_por_cambio_documental` por cada admision afectada para mantener consistencia del informe tecnico (ver Riesgo R3).
- **Admision-side (deshabilitar para org-docs):**
  - `documento_row.html`: para docs con `archivo_organizacion_origen` (origen org), el GDE se muestra **solo lectura** con leyenda "Se gestiona desde el Legajo de la Organizacion". Mantener editable solo para docs nativos.
  - Deprecar `actualizar_numero_gde_organizacion_admision` (650 web_views) y su ruta: devolver 410 Gone o remover. `actualizar_numero_gde_archivo` se mantiene **solo** para docs nativos (validar que el archivo no tenga `archivo_organizacion_origen`).
- **Autocomplete informe tecnico:** ajustar `_ultimo_numero_gde` ([admisiones/forms/admisiones_forms.py:16](../../admisiones/forms/admisiones_forms.py)) para leer el GDE de org-docs desde `ArchivoOrganizacion.numero_gde` (via procedencia) en lugar de `NumeroGdeOrganizacion`.
- **`subir_documento_organizacion` (linea 877):** hoy limpia `numero_gde=None` al re-subir. Mantener (un documento nuevo vuelve a estado no-Aceptado, GDE oculto), pero al replicar tras nueva aceptacion el GDE bajara de nuevo. Documentar.
- **Tests:** editar GDE en org Aceptado replica a admisiones materializadas; no editable si no Aceptado; admision-side queda solo lectura para org-docs y editable para nativos; backfill desde NumeroGdeOrganizacion; conflicto loguea.

### Req 1 — Advertencia ante cambios de documentacion (generaliza el resync)
**Objetivo:** mostrar la advertencia + 2 opciones + confirmacion cuando la documentacion del legajo cambia respecto de lo que la admision ya tenia, listando los documentos modificados.

- **Modelo/migracion (`admisiones`):** nuevo modelo de snapshot documental:
  ```python
  class AdmisionDocOrgSnapshot(models.Model):
      admision = FK(Admision, on_delete=CASCADE, related_name="snapshots_doc_org")
      documentacion_organizacion = FK("organizaciones.DocumentacionOrganizacion",
                                      on_delete=CASCADE, null=True, blank=True)  # slot catalogo
      archivo_organizacion = FK("organizaciones.ArchivoOrganizacion",
                                on_delete=SET_NULL, null=True, blank=True)        # personalizados / ref actual
      token = CharField(max_length=255)   # ver D2
      synced_at = DateTimeField(auto_now=True)
      class Meta:
          constraints = [UniqueConstraint(
              fields=["admision", "documentacion_organizacion", "archivo_organizacion"],
              name="unq_snapshot_doc_org")]
  ```
  Migracion: backfill inicializando el snapshot al estado actual del legajo para todas las admisiones activas (asi arrancan "en sync"; cubre req 1.6 — solo dispara ante cambios POSTERIORES).
- **Servicio:**
  - `_construir_tokens_org_actuales(admision) -> dict[slot_key, token]`: estado actual del legajo para la categoria de la admision + personalizados.
  - `admision_documentacion_desactualizada(admision) -> (bool, list[labels])`: compara snapshot vs actual; devuelve los labels de docs **agregados / modificados / con cambio de estado** (incluye `Pendiente→Aceptado`). Lazy-init del snapshot si vacio (patron `_asegurar_snapshot_tipo_entidad`).
  - Generalizar `resync_admision_desde_organizacion`: ademas de tipo, refresca el snapshot documental tras re-materializar. `aceptar_desincronizacion_admision`: refresca AMBOS snapshots sin tocar documentos.
  - Refrescar el snapshot documental en: `create_admision`, `resync`, `aceptar`, y tras materializar en `OrganizacionUpdateView.form_valid`.
- **Contexto:** `_build_response_update_context` expone `desync_motivo`, `documentos_modificados` (lista de labels) ademas de los flags actuales.
- **Template:** generalizar el modal (41-103) para:
  - Encabezado segun motivo: documentacion → "La Documentacion relacionada a la Organizacion fue actualizada desde el Legajo de la Organizacion. Para continuar con la admision debe seleccionar una de las siguientes opciones".
  - Mostrar el **listado de labels** de `documentos_modificados`.
  - Mismas 2 opciones y mismos textos de confirmacion (paso 2) ya implementados.
- **JS:** reusar `admisionResyncConvenio.js` (el endpoint `resync_convenio_admision` ya cubre actualizar/continuar). Sin cambios de endpoint.
- **Tests:** cambio de vencimiento/archivo/estado dispara la advertencia con el label correcto; `Pendiente→Aceptado` dispara (1.7); "Actualizar" re-materializa y limpia el banner; "Continuar" silencia hasta el proximo cambio; admisiones nuevas arrancan en sync (1.6); personalizados nuevos en org disparan (interaccion Req 4).

---

## 4. Orden de implementacion y dependencias

```
Fase 0 (procedencia + helper)  ──┬─> Req 3 (GDE) ──┐
                                 │                 ├─> Req 1 (advertencia)
Req 4 (doc adicional) ───────────┴─────────────────┘
Req 2 (acta)  ── independiente (puede ir en paralelo, antes de Req 1)
```

- **Fase 0** primero: la FK de procedencia la consumen Req 3 (replicacion exacta) y Req 1 (diff y origen).
- **Req 4** antes de Req 1: para que el snapshot/diff y la materializacion ya contemplen personalizados.
- **Req 2** independiente; conviene antes de Req 1 para que el Acta ya no sea org-doc cuando se construya el snapshot.
- **Req 3** antes de Req 1: el token del snapshot excluye GDE, pero la procedencia y la deprecacion de NumeroGdeOrganizacion deben estar resueltas para evitar entrelazar conflictos de template (`documento_row.html`).
- **Req 1** al final: integra todo.

Cada fase es un PR independiente a `development`. Si un PR crece demasiado, separar modelo+migracion de UI.

---

## 5. Migraciones (consolidado)

| App | Migracion | Tipo | Reversible |
|---|---|---|---|
| admisiones | `ArchivoAdmision.archivo_organizacion_origen` (FK nullable) + backfill por alias | schema + data | si (drop col) |
| organizaciones | `ArchivoOrganizacion.documentacion` nullable + `nombre_personalizado` | schema | si |
| organizaciones | quitar "Acta..." del catalogo + soft-delete archivos del acta | data | no-op reverse |
| admisiones | backfill `ArchivoOrganizacion.numero_gde` desde `NumeroGdeOrganizacion`/`ArchivoAdmision` (resolucion por mas reciente, log de conflictos) | data | no-op reverse |
| admisiones | `AdmisionDocOrgSnapshot` + backfill al estado actual del legajo | schema + data | si (drop tabla) |

Todas no destructivas salvo la eliminacion del catalogo del Acta (Req 2) y el soft-delete de sus archivos. `NumeroGdeOrganizacion` **no se borra** (D5).

Validar siempre: `python manage.py makemigrations --check --dry-run` y aplicar en orden.

---

## 6. Riesgos y consecuencias

- **R1 (Alto) — Reversion del #1605:** el Req 3 deshace la decision "GDE por admision". `NumeroGdeOrganizacion` queda deprecado pero presente. Si dos admisiones tenian GDE distinto para el mismo doc, el backfill **pierde** una de las variantes (se loguea). Mitigacion: log + entrada en el changelog + revisar el log post-deploy.
- **R2 (Alto) — Costo del diff (Req 1):** evaluar la advertencia en cada render de la admision implica comparar snapshot vs legajo. Mitigacion: `select_related/prefetch` de los `ArchivoOrganizacion` vigentes + indices; cache por request. Evitar N+1 (patron ya documentado en [docs/registro/cambios/2026-04-20-admisiones-ajax-actualizar-estado-n-plus-one.md](../registro/cambios/2026-04-20-admisiones-ajax-actualizar-estado-n-plus-one.md)).
- **R3 (Medio) — Efecto colateral de la replicacion de GDE:** con "replicar a todas", editar el GDE en org puede resetear el informe tecnico de muchas admisiones (via `_limpiar_if_gde_admision_por_cambio_documental`). Es consecuencia de la decision confirmada. Mitigacion: aplicar el reset solo a admisiones en estados editables; loguear; documentar para soporte.
- **R4 (Medio) — Tension interna del spec:** Req 1 admite documentacion divergente por admision, pero Req 3 centraliza el GDE. Quedan coherentes si el GDE se replica solo a docs aun ligados al legajo; documentar el limite (un doc ya "desincronizado" por el usuario que eligio "Continuar" igual recibira el GDE nuevo si sigue materializado).
- **R5 (Bajo) — HOTFIX vs tamano:** el issue es HOTFIX pero implica ~5 migraciones y reversion de logica. Mitigacion: 4 PRs chicos y revisables; priorizar Req 2 y Req 4 (bajo riesgo) para entregar valor temprano.
- **R6 (Bajo) — Aflojar la FK del catalogo (Req 4):** `documentacion` pasa de PROTECT a nullable/SET_NULL. Revisar queries que asumen `documentacion` no nulo en `organizaciones/views.py` y serializadores.

---

## 7. Validacion

Por PR:
- `pytest organizaciones admisiones --tb=short -q` (Docker-first; ver [reference_sisoc_validation]).
- `python manage.py makemigrations --check --dry-run` y `python manage.py check`.
- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 validate`.

Tests nuevos por requerimiento (ver cada seccion). Manual:
1. **Req 4:** alta de doc adicional en org → aparece en legajo → se materializa en admision nueva.
2. **Req 2:** el Acta no esta en el legajo; aparece como doc de admision convenio 3; convenios 1/2 no la muestran.
3. **Req 3:** GDE editable en org Aceptado → replica a admisiones; admision-side solo lectura para org-docs y editable para nativos.
4. **Req 1:** cambiar vencimiento/estado/archivo de un doc del legajo → advertencia con el label correcto en admisiones iniciadas; "Actualizar" re-materializa, "Continuar" silencia; admisiones nuevas sin advertencia.

---

## 8. Registro (al cerrar cada PR)

- `docs/registro/cambios/2026-06-01-issue-1799-<req>.md` por requerimiento.
- `docs/registro/decisiones/2026-06-01-gde-origen-organizacion.md` (revierte la decision del #1605; referenciar `2026-05-22-numero-gde-propiedad-admision.md`).
- `docs/registro/decisiones/2026-06-01-advertencia-doc-org-snapshot.md` (mecanismo de snapshot/token del Req 1).

---

## 9. Supuestos

1. El mapeo categoria↔convenio (`CATEGORIA_ORGANIZACIONAL_POR_TIPO_CONVENIO`) y el alias por nombre siguen siendo la fuente de verdad para resolver org-doc ↔ admision-doc. La FK de procedencia (D1) reduce la dependencia de la heuristica a futuro.
2. "Replicar a todas las admisiones relacionadas" (Req 3) incluye solo admisiones activas (`enviada_a_archivo=False`); las archivadas no se tocan.
3. El backfill de GDE prioriza el valor mas reciente ante conflicto; las perdidas se loguean (no hay forma univoca de revertir un modelo 1→N).
4. La eliminacion del Acta del catalogo de Organizacion es aceptable (no se preserva historico de ese slot en el legajo), coherente con los resets destructivos que el #1605 ya aplica al legajo.
5. El snapshot documental (Req 1) se inicializa al estado actual para admisiones existentes: no dispara advertencias retroactivas, solo ante cambios posteriores (lectura de req 1.6).
