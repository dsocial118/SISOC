# Correcciones de issues reabiertos en admisiones, prestaciones y rendiciones

## Fecha

2026-08-12

## Objetivo

Resolver las diferencias detectadas al reprobar los issues #2234, #2252, #2259 y #2079, manteniendo compatibilidad con datos legados y con la PWA.

## Alcance

- Campo condicional y variable documental para el Informe Técnico de renovaciones.
- Visualización en SISOC de certificaciones de prestaciones creadas sin PDF.
- Gestión visual de proyectos y rendiciones dentro del legajo de Organización.
- Continuidad de las etapas Territorial y Auditoría ante validaciones y subsanaciones.
- Formulario único para el cierre administrativo de Auditoría.

## Archivos tocados

- `admisiones/forms/admisiones_forms.py`, modelo, migración `0078`, servicio DOCX y template del informe.
- `comedores/views/comedor.py` y templates de detalle e historial de certificaciones.
- `organizaciones/forms.py`, `views.py`, templates y tests.
- `rendicioncuentasmensual/services.py`, template de detalle y tests de servicios.
- `AGENT_REPO_MAP.md`.

## Cambios realizados

- Se incorporó el campo de Informe Técnico Complementario cuando una renovación modifica prestaciones y se registró como variable disponible para DOCX.
- Las certificaciones mensuales sin archivo PDF dejaron de excluirse de las vistas de SISOC; se informan como no disponibles para descarga.
- La edición de proyectos usa un listado alineado, modal de alta y eliminación individual, conservando el contrato CSV del formulario.
- El detalle de Organización muestra proyectos como pills y contempla rendiciones asociadas directamente a `ProyectoOrganizacion`, además del vínculo legado por comedor.
- El detalle de una rendición desde Organización admite ambos tipos de asociación y conserva el control de visibilidad.
- La revisión documental ya no cambia el estado global al observar o validar cada archivo: la etapa se resuelve al finalizarla.
- Territorial mantiene la rendición En revisión al pasar a Auditoría; sólo la finalización satisfactoria de Auditoría marca la presentación como finalizada.
- Las subsanaciones conservan la etapa que las originó. Al reanudar Auditoría se preservan los documentos ya validados y sólo el primer inicio reinicia los documentos heredados desde Territorial.
- El cierre administrativo de Auditoría quedó consolidado en un formulario con monto, acta, resultado y observaciones condicionales.
- Las notificaciones y consultas por proyecto priorizan la relación actual y conservan fallback por código de proyecto para registros legados.

## Supuestos

- Los registros de certificación sin PDF son válidos porque el endpoint PWA permite crearlos cuando no existe una fuente documental para generar el archivo.
- `RendicionCuentaMensual.proyecto` es la asociación principal; `comedor.codigo_de_proyecto` continúa soportado para datos anteriores.
- La publicación del frontend móvil se gestiona en SISOC-Mobile y quedó realizada en `main` mediante el commit `6163f50`.

## Validaciones ejecutadas

- Suite focalizada de admisiones, certificaciones web, organizaciones y servicios de rendiciones: 119 tests aprobados.
- Suite completa: 3982 tests aprobados y 10 omitidos.
- Formato Python con Black y consistencia del diff sin errores.
- Comparación con `origin/development`: rama basada en el mismo commit antes de preparar el PR.

## Pendientes / riesgos

- Aplicar la migración `admisiones.0078` en los ambientes de despliegue.
- Verificar que HML despliegue versiones coordinadas de SISOC y SISOC-Mobile y que ambos apunten a la base correspondiente.
- `djlint` local no llegó a completar el chequeo de los seis templates dentro de dos ejecuciones de 120 segundos; queda cubierto por los checks del PR.
