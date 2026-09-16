# 2026-09-15 - VPSL: creación de itinerarios en cualquier provincia

## Cambio

- Se agrega `ver_para_ser_libre.create_itinerarios_any_province_vpsl`. Este permiso habilita la creación de itinerarios en cualquier provincia, aun sin el permiso estándar `add_itinerariovpsl`.
- Quien lo use debe tener una provincia asignada en su perfil. El permiso no exige que el perfil esté marcado como usuario provincial.
- En el alta, Provincia pasa a ser un Select2 con todas las provincias ordenadas alfabéticamente. La búsqueda de sedes tentativas usa la provincia elegida y se limpia al cambiarla. El servidor rechaza sedes que no correspondan a la provincia del itinerario. El filtro de jurisdicción exige coincidencia exacta, evitando mezclar Buenos Aires con Ciudad de Buenos Aires.
- El filtro opcional de localidad se actualiza con las localidades de las sedes de la provincia elegida.
- El creador puede consultar sus propios itinerarios de otras provincias en el listado y detalle. El permiso no le da acceso a los itinerarios ajenos de esas provincias; para eso sigue existiendo `view_all_itinerarios_vpsl`.

## Compatibilidad

Sin el permiso nuevo, el alta conserva la provincia asignada bloqueada y el servidor ignora otra provincia enviada por POST. Los permisos de modificación, eliminación, aprobación y exportación mantienen sus controles existentes.

## Validación

Tests acotados de creación en `ver_para_ser_libre/tests/test_workflow.py`.
