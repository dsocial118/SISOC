# Ajustes en admisiones, organizaciones, expedientes y relevamientos

## Fecha
2026-05-21

## Objetivo
Resolver inconsistencias detectadas en flujos de admisiones, legajo de organización, expedientes de pago, detalle de comedor y listado de relevamientos.

## Alcance
Se incluyeron cambios visibles y de comportamiento en:
- admisiones y documentación asociada
- legajo de organización y documentación
- expedientes de pago
- detalle de comedor
- listado de relevamientos

## Archivos tocados
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/templates/admisiones/admisiones_tecnicos_form.html`
- `admisiones/templates/admisiones/includes/documento_row.html`
- `admisiones/views/web_views.py`
- `comedores/services/comedor_service/impl.py`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/views/comedor.py`
- `expedientespagos/services.py`
- `expedientespagos/views.py`
- `organizaciones/templates/organizacion_detail.html`
- `organizaciones/templates/organizacion_form.html`
- `organizaciones/templates/organizaciones/documentacion_historial.html`
- `organizaciones/templates/organizaciones/partials/documentacion_organizacion_row.html`
- `organizaciones/views.py`
- `relevamientos/templates/relevamiento_list.html`
- `static/custom/js/organizacionesDocumentos.js`

## Cambios realizados
- Se corrigió la etiqueta visible `Anio` a `Año` en el detalle de comedor.
- Se reubicó la card `Transacciones - Nación Servicios` debajo de `Detalles de Admisión`.
- Se ordenaron expedientes de pago por período descendente, del más reciente al más antiguo.
- Se corrigió un paréntesis sobrante que provocaba error de sintaxis en `comedores/views/comedor.py`.
- El tipo de convenio de una admisión se precarga desde el tipo de entidad de la organización y deja de ser editable por el técnico.
- La pantalla de selección de convenio muestra el tipo de entidad de la organización como dato no editable.
- El formulario de organización advierte cuando se modifica el tipo de entidad.
- La documentación de organización permite adjuntar archivos Excel y Word.
- El número GDE de documentos de organización deja de editarse en el legajo y se gestiona desde la admisión.
- La admisión permite gestionar números GDE para documentos propios y documentos provenientes de organización.
- La admisión muestra la fecha de vencimiento configurada en el legajo organización para documentos de origen organización.
- Se sincroniza el estado documental de la admisión cuando se materializan documentos de organización aceptados.
- Organización usa un modal de observaciones obligatorio al rectificar documentación, alineado con el flujo existente en admisión.
- El listado de relevamientos muestra el Número de IF como texto fijo y habilita la edición solo mediante el botón `Actualizar IF`.

## Supuestos
- `Asociación de Hecho` en tipo de entidad se equipara a `Organización Base` en tipo de convenio.
- Los documentos de organización deben seguir gestionándose desde el legajo de organización, salvo el número GDE solicitado para admisión.
- El listado de relevamientos mantiene el guardado por POST existente; el cambio es de presentación y habilitación de edición.

## Validaciones ejecutadas
- `git diff --check`
- `docker compose exec django python manage.py check`

## Pendientes / riesgos
- No se ejecutó la validación integral `scripts/ai/codex_run.ps1 validate`.
- No se ejecutaron tests automatizados específicos.
- La sesión se cerró sobre la branch existente `Fixes-20-05-26`; no se creó un worktree nuevo porque los cambios ya estaban acumulados en esta rama.
