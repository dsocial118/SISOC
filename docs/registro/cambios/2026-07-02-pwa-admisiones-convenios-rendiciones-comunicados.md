# Cambios PWA, admisiones, convenios, rendiciones y comunicados

## Fecha
2026-07-02

## Objetivo
Resolver ajustes funcionales acumulados para la app mobile/PWA y SISOC web vinculados con conformidad de prestaciones, usuarios PWA, relevamientos, convenios, informes tecnicos, rendiciones y comunicados.

## Alcance
- PWA mobile para espacios, usuarios, relevamientos, mensajes, nomina y prestaciones conveniadas.
- Web SISOC para admisiones, informes tecnicos, convenios PNUD/Abordaje, rendiciones y comunicados.
- Migraciones de admisiones, comedores y comunicados necesarias para nuevos campos y reparaciones de bases locales.
- Menu lateral web y filtros avanzados del listado global de rendiciones.

## Archivos tocados
- `admisiones/models/admisiones.py`
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/templates/admisiones/admisiones_detalle.html`
- `admisiones/templates/admisiones/admisiones_tecnicos_form.html`
- `admisiones/urls/web_urls.py`
- `admisiones/views/web_views.py`
- `admisiones/migrations/0064_admision_personas_conveniadas_nomina.py`
- `admisiones/migrations/0065_admision_vigente_pwa.py`
- `admisiones/migrations/0066_repair_informetecnico_missing_columns.py`
- `admisiones/migrations/0067_repair_informetecnicopdf_missing_columns.py`
- `comedores/admin.py`
- `comedores/api_serializers.py`
- `comedores/api_views.py`
- `comedores/forms/convenio_pnud_form.py`
- `comedores/models.py`
- `comedores/services/comedor_service/impl.py`
- `comedores/templates/comedor/comedor_convenio_pnud_form.html`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/utils.py`
- `comedores/views/comedor.py`
- `comedores/migrations/0046_comedordatosconveniopnud_prestaciones.py`
- `comunicados/api_views.py`
- `comunicados/forms.py`
- `comunicados/models.py`
- `comunicados/permissions.py`
- `comunicados/views.py`
- `comunicados/migrations/0009_comunicado_organizaciones.py`
- `core/services/favorite_filters/config.py`
- `pwa/services/mensajes_service.py`
- `pwa/services/nomina_service.py`
- `rendicioncuentasmensual/filter_config.py`
- `rendicioncuentasmensual/services.py`
- `rendicioncuentasmensual/templates/rendicioncuentasmensual_global_list.html`
- `rendicioncuentasmensual/views.py`
- `static/custom/js/admisionesactualizarestado.js`
- `static/custom/js/comunicadosForm.js`
- `templates/comunicados/comunicado_form.html`
- `templates/includes/sidebar/new_opciones.html`
- `templates/includes/sidebar/opciones.html`
- `tests/test_comedores_utils_unit.py`
- `tests/test_pwa_comedores_api.py`
- `users/api_serializers.py`
- `users/services_pwa.py`
- `mobile/src/features/home/SpaceDetailPage.tsx`
- `mobile/src/features/home/SpacePrestacionesConveniadasPage.tsx`
- `mobile/src/features/home/SpaceUsersPage.tsx`

## Cambios realizados
- La PWA permite registrar conformidad de prestaciones sobre cualquier periodo calendario mes/anio, con unicidad por espacio y periodo.
- El selector de anio de conformidad en PWA pasa a desplegable con rango desde tres anios atras hasta cuatro anios adelante.
- El alta de usuarios PWA admite email vacio y emails repetidos; la PWA muestra el email como opcional.
- La PWA ajusta datos visibles de relevamiento: oculta judicializado/dupla, prestaciones "espera" y excepcion, y usa terminologia de Espacio.
- La PWA oculta "Monto total conveniado" a usuarios asociados por Espacio y lo conserva para accesos por Organizacion.
- La nomina alimentaria PWA aplica tope por personas conveniadas: Alimentar Comunidad usa el campo en Admision, y Abordaje/PNUD usa Datos del Convenio.
- Admision tecnica suma el campo "Personas conveniadas nomina" con el mismo UX de carga/edicion y toast que "Numero de convenio".
- IT Complementario queda disponible con IT finalizado y Prestaciones Conveniadas usa el complementario validado como override del IT original.
- Admision suma marca "Vigente PWA"; la PWA usa esa admision como referencia y el detalle de comedor muestra check de convenio vigente.
- Se agregan migraciones de reparacion idempotente para columnas faltantes de `InformeTecnico` e `InformeTecnicoPDF` en bases locales parcialmente migradas.
- Convenio PNUD/Abordaje suma cuadro semanal de prestaciones por convenio y web/PWA lo usan para prestaciones mensuales y monto.
- La tabla de Prestaciones del legajo usa Convenio PNUD/Abordaje como fuente cuando corresponde.
- El listado global de Rendiciones suma barra de filtros avanzados con favoritos.
- Rendiciones se mueve del menu de Comedores/Legajos al menu de Organizaciones en ambos sidebars.
- Comunicados suma subtipo "Comunicacion a Organizaciones", selector multiple de organizaciones y visibilidad PWA por organizacion del espacio.
- La etiqueta "Cantidad Modulos" pasa a "Cantidad Modulos Mensuales" en Datos del Convenio SISOC y PWA.
- La PWA reemplaza "Usuarios PWA" por "Usuarios responsables del Espacio Comunitario" en tarjeta y detalle.
- En espacios Alimentar Comunidad, los subusuarios PWA no pueden recibir el permiso "Rendicion de Cuentas" y la UI no lo muestra.

## Supuestos
- Los datos demo creados localmente para comedores FAST no forman parte del cambio versionado.
- La reparacion de migraciones apunta a bases locales donde el squash quedo parcialmente aplicado; no reemplaza el historial normal de migraciones.
- En comunicados a organizaciones, la PWA muestra el mensaje al espacio cuando su organizacion coincide con una organizacion destinataria.

## Validaciones ejecutadas
- `docker compose exec django python manage.py check`
- `docker compose exec django pytest tests/test_pwa_comedores_api.py tests/test_comedores_utils_unit.py`
- `npm run build` en `mobile/`

## Pendientes / riesgos
- `npm run build` finalizo correctamente, pero Vite informo el warning existente de chunks mayores a 500 kB.
- Las migraciones `admisiones.0066`, `admisiones.0067`, `comedores.0046` y `comunicados.0009` fueron aplicadas durante la sesion en la base local.
