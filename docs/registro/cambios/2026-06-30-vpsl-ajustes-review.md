# 2026-06-30 - VPSL: ajustes por review

## Cambio

- Se corrige la busqueda de itinerarios por estado para que compare contra la etiqueta visible del estado y no solo contra el valor persistido en base.
- Se agregan fallbacks a las variables CSS usadas por Select2, ya que el dropdown puede renderizarse fuera del arbol de `.vpsl-page`.
- Se ajusta la visibilidad de acciones en el detalle de jornada:
  - `Habilitar` solo se muestra cuando la jornada esta en estado habilitable.
  - `Cerrar jornada` solo se muestra cuando el estado de la jornada permite iniciar el cierre.
  - `Nuevo registro` se mantiene visible como accion deshabilitada cuando no puede usarse, con explicacion del prerequisito.

## Motivo

Responder observaciones de review sin revertir el redisenio UX aprobado del modulo Ver Para Ser Libres.

## Alcance

- No cambia el flujo de estados del workflow.
- No agrega nuevos permisos ni endpoints.
- Mantiene el layout visual nuevo y solo corrige comportamiento/feedback de acciones.

## Validacion

- `python manage.py check`
- `pytest ver_para_ser_libre/tests/test_workflow.py::test_itinerario_list_busca_estado_por_etiqueta_visible -q`
- `pytest ver_para_ser_libre/tests/test_workflow.py::test_jornada_detail_muestra_acciones_segun_estado -q`
- `pytest ver_para_ser_libre -q`
