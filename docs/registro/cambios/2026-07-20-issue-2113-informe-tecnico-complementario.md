# Issue 2113: mejoras del Informe Técnico Complementario

## Fecha

2026-07-20

## Objetivo

Permitir gestionar el Informe Técnico Complementario desde Acompañamiento y
alinear su presentación y advertencias con el flujo real de Admisiones.

## Alcance

- Acceso desde el convenio seleccionado en Acompañamiento.
- Presentación agrupada según las secciones del Informe Técnico original.
- Advertencia condicionada a una solicitud efectiva o rectificación.
- Retorno al flujo desde el cual se abrió el informe.

## Archivos tocados

- `acompanamientos/views.py`
- `acompanamientos/templates/acompañamiento_detail.html`
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/services/informes_service/impl.py`
- `admisiones/views/web_views.py`
- `admisiones/templates/admisiones/admisiones_tecnicos_form.html`
- `admisiones/templates/admisiones/informe_tecnico_complementario_detalle.html`
- Tests unitarios relacionados en `tests/`

## Cambios realizados

- El Acompañamiento ofrece el acceso al Informe Técnico Complementario del
  informe finalizado correspondiente a la admisión seleccionada.
- El acceso se limita a usuarios técnicos y conserva la admisión/convenio al
  regresar o enviar el informe.
- Los campos se muestran en bloques equivalentes al Informe Técnico original,
  manteniendo la selección manual de cada modificación.
- La alerta deja de mostrarse por la mera finalización del Informe Técnico y se
  reserva para solicitudes de Legales o informes a rectificar.
- Se agregaron pruebas para selección de admisión, permisos, agrupación,
  contexto de la vista y condición de la advertencia.

## Supuestos

- El Informe Técnico Complementario se confecciona sobre el último informe
  finalizado de la admisión seleccionada.
- La advertencia representa una acción requerida; la disponibilidad del botón
  continúa siendo independiente para permitir iniciar el informe.

## Validaciones ejecutadas

- 93 pruebas focalizadas: correctas.
- `black --check` sobre los archivos Python modificados: correcto.
- `python manage.py check`: sin observaciones.
- `git diff --check`: correcto.
- `djlint --check` sobre los templates modificados: correcto.
- `pylint` focalizado encontró deuda preexistente del módulo; no señaló una
  regresión específica asociada a este cambio.

## Pendientes / riesgos

- Confirmar visualmente el formulario con informes de tipo base y jurídico.
