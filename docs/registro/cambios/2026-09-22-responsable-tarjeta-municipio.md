# 2026-09-22 - Municipio en el formulario de Responsable de la Tarjeta

## Contexto
- El formulario `comedor/responsable_tarjeta_form.html` no filtraba localidades: cargaba el script
  de cascada dentro de `{% block extra_js %}`, un bloque que no existe en `includes/base.html`
  (el bloque real es `customJS`), por lo que el JS nunca se renderizaba.
- Además faltaba el nivel intermedio de Municipio, presente en el alta de Organizaciones.

## Cambios aplicados
- `comedores/models.py`: nuevo FK `Comedor.responsable_tarjeta_municipio` (`Municipio`, PROTECT,
  null/blank, `related_name="comedores_responsable_tarjeta"`).
- `comedores/migrations/0061_comedor_responsable_tarjeta_municipio.py`: AddField correspondiente.
- `comedores/forms/comedor_form.py` (`ResponsableTarjetaComedorForm`): agrega el campo y reemplaza
  el filtrado provincia→localidad por la cascada provincia→municipio→localidad con
  `popular_campos_ubicacion()`, siguiendo el patrón de `OrganizacionForm`. `clean()` valida que
  municipio pertenezca a la provincia y localidad al municipio (o a la provincia si no hay municipio).
- `comedores/templates/comedor/responsable_tarjeta_form.html`: render por campo con loaders,
  bloque `customJS` (en lugar del inexistente `extra_js`) e init de `setupUbicacionSelects`
  con `ajax_load_municipios` / `ajax_load_localidades`.
- `comedores/templates/comedor/comedor_detail.html`: la tarjeta resumen muestra Municipio.
- `comedores/tests/test_responsable_tarjeta_form.py`: cubre la cascada, el municipio ajeno, la
  precarga desde la localidad y que la página de edición cargue `ubicacionSelects.js` (regresión #2491).

## Impacto esperado
- Al elegir provincia se cargan sus municipios y, al elegir municipio, sus localidades.
- Los datos ya cargados siguen siendo válidos: `responsable_tarjeta_municipio` queda en `NULL` y
  la localidad existente se preserva (la validación cae al chequeo por provincia cuando no hay municipio).
- Sin backfill: para esos registros el formulario precarga el municipio desde
  `responsable_tarjeta_localidad.municipio` y el detalle lo muestra con el mismo fallback, así el
  select encadenado no queda vacío ni obliga a re-elegir la localidad.

## Validación
- `pytest comedores/tests/test_responsable_tarjeta_form.py` (2 passed).
- `python manage.py makemigrations --check --dry-run` sin cambios pendientes.
- `black` y `djlint --check` sobre los archivos tocados.

## Riesgos y rollback
- Riesgo principal: registros previos con localidad cargada y municipio vacío; se contempla en `clean()`.
- Rollback: revertir el commit y aplicar `migrate comedores 0060`.
