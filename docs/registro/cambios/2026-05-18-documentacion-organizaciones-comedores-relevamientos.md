# Documentacion organizacional, legajo comedor y relevamientos

## Fecha
2026-05-18

## Objetivo
Consolidar ajustes funcionales sobre documentacion de organizaciones, reutilizacion documental en admisiones, legajo de comedor, relevamientos y permisos de edicion para comedores PAC.

## Alcance
- Documentacion organizacional versionada, con carga, estados, GDE, vencimiento, observaciones e historial.
- Reutilizacion de documentacion organizacional en admisiones y congelado al finalizar informe tecnico.
- Resumen de mes de ejecucion en legajo de comedor PAC y filtro/listado por mes de ejecucion.
- Nuevo campo Numero de IF para relevamientos, editable desde el listado de relevamientos del comedor.
- Restriccion de edicion manual de estados de comedor PAC para usuarios no coordinadores.

## Archivos tocados
- `organizaciones/models.py`
- `organizaciones/admin.py`
- `organizaciones/views.py`
- `organizaciones/urls.py`
- `organizaciones/templates/organizacion_detail.html`
- `organizaciones/templates/organizacion_list.html`
- `organizaciones/templates/organizaciones/documentacion_historial.html`
- `organizaciones/templates/organizaciones/partials/documentacion_organizacion_row.html`
- `organizaciones/templates/organizaciones/partials/organizacion_rows.html`
- `organizaciones/migrations/0012_documentacion_organizacion.py`
- `organizaciones/migrations/0013_archivoorganizacion_numero_gde.py`
- `static/custom/js/organizacionesDocumentos.js`
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/services/informes_service/impl.py`
- `admisiones/templates/admisiones/includes/documento_row.html`
- `comedores/forms/comedor_form.py`
- `comedores/services/comedor_service/impl.py`
- `comedores/services/filter_config/impl.py`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/views/comedor.py`
- `templates/components/comedor_table.html`
- `relevamientos/models.py`
- `relevamientos/serializer.py`
- `relevamientos/templates/relevamiento_list.html`
- `relevamientos/views/web_views.py`
- `relevamientos/migrations/0007_relevamiento_numero_if.py`
- `templates/includes/sidebar/new_opciones.html`
- `templates/includes/sidebar/opciones.html`

## Cambios realizados
- Se agregaron modelos y migraciones para documentacion organizacional y archivos versionados.
- Se agrego numero GDE, fecha de vencimiento, historial de versiones, observaciones y cambios de estado para documentos de organizaciones.
- Se limito el flujo documental de organizaciones a la dupla asignada al comedor vinculado y se separaron acciones permitidas para tecnico y abogado.
- Se agrego pagina separada para historial documental de organizacion.
- Se ocultaron acciones de edicion/eliminacion de organizacion para usuarios tecnico/abogado de dupla.
- Se preparo la reutilizacion de documentos organizacionales en admisiones cuando no exista documento previo en admision.
- Se congela la documentacion organizacional en admision al finalizar el informe tecnico.
- Se agrego card de Mes de ejecucion al final del legajo de comedor PAC, usando el ultimo expediente de pago.
- Se agrego columna y filtro avanzado Mes de ejecucion en el listado de comedores.
- Se agrego campo `numero_if` a `Relevamiento`, editable desde `/comedores/<id>/relevamiento/listar`.
- Se excluyo `numero_if` del serializer de relevamientos para no mezclarlo con la ida/vuelta de Gestionar.
- Se deshabilitaron Estado general, Subestado y Motivo en edicion de comedores PAC para usuarios que no sean Superadmin o coordinadores.

## Supuestos
- El historial documental de organizaciones se conserva creando una nueva version por cada adjunto aceptado.
- Los documentos no aceptados se pisan si se carga uno nuevo.
- `ExpedientePago.mes_convenio` se reutiliza como Mes de ejecucion.
- La clasificacion documental organizacional se resuelve por tipo/subtipo de entidad y puede requerir ajuste si los nombres productivos difieren.

## Validaciones ejecutadas
- `docker compose exec django python manage.py check`: sin issues.
- `docker compose exec django python manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- `git diff --check`: sin errores; reporto solo advertencias de normalizacion CRLF/LF en archivos ya modificados.

## Pendientes / riesgos
- En una iteracion posterior conviene enlazar admisiones contra una version exacta de `ArchivoOrganizacion`.
- No se ejecutaron tests unitarios o de integracion especificos.
