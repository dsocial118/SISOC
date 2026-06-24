# PWA mobile permisos operativos y actividades web

## Fecha
2026-06-24

## Objetivo
Cerrar los ajustes pendientes sobre permisos operativos de usuarios SISOC Mobile y replicar en Web la carga de actividades del comedor usada actualmente en la PWA mobile.

## Alcance
- Edicion y alta web de usuarios mobile principales.
- Visualizacion web de subusuarios mobile creados por un usuario principal.
- Alta y edicion web de actividades de espacios PNUD desde el detalle del comedor.
- Validaciones de horarios de actividades equivalentes al flujo mobile.

## Archivos tocados
- `users/forms.py`
- `users/templates/user/user_form.html`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/urls.py`
- `comedores/views/__init__.py`
- `comedores/views/comedor.py`
- `comedores/forms/actividad_espacio_pwa_form.py`
- `comedores/views/actividad_espacio_pwa.py`
- `comedores/templates/comedor/actividad_espacio_pwa_form.html`

## Cambios realizados
- Los permisos operativos PWA ocultos volvieron a mostrarse como checks en alta y edicion web de usuarios mobile principales.
- Los permisos operativos PWA de usuarios mobile principales quedaron tildables y se guardan segun lo seleccionado.
- El listado de subusuarios mobile en la edicion web del usuario principal muestra los permisos con nombres legibles.
- Se habilito desde el detalle web del comedor la creacion de actividades para espacios PNUD usando el boton existente de Actividades.
- Se agrego edicion web de actividades del comedor con la misma base de reglas que mobile: programa PNUD, permiso de colaboradores, horario obligatorio, control de solapamientos y auditoria mediante el servicio PWA existente.
- El formulario web de actividades permite cargar varias filas de dia y horario para una misma actividad.
- La carga web deduplica combinaciones repetidas de dia y horario y guarda un slot por cada fila valida.
- En edicion, Web replica mobile: actualiza el primer slot y crea slots adicionales si se agregan mas filas.

## Supuestos
- El permiso usado para gestionar actividades del comedor en Web es `pwa.manage_colaboradores_pwa`, igual que el flujo mobile de actividades PNUD.
- La auditoria de actividades debe seguir pasando por los servicios PWA existentes.
- Los checks operativos PWA de usuarios principales pueden modificarse manualmente desde SiSoc Web.

## Validaciones ejecutadas
- `python -c "import ast, pathlib; ..."` sobre archivos Python tocados: OK.
- `docker compose exec django python manage.py check`: OK, sin issues.

## Pendientes / riesgos
- No se ejecutaron `black` ni `djlint` por instruccion explicita.
- No se ejecutaron tests automatizados ni build en este cierre.
