# Cambios Mobile Formación y Admisiones

## Fecha
2026-05-05

## Objetivo
Implementar la sección Formación dinámica en mobile con ABM en web, y ajustar la edición de número de expediente en Admisiones (Técnicos) con reglas de visibilidad y UX solicitadas.

## Alcance
- Mobile: renombre a Formación, consumo dinámico de cursos, separación entre cursos comunes y recomendados.
- Web Comedores: ABM de Cursos App Mobile con borrado lógico, imagen, programa objetivo y check de recomendado.
- API PWA: endpoint de formación y serializer para cursos.
- Admisiones: edición de número de expediente solo en pantalla de Técnicos, con tooltip contextual y condiciones de visibilidad.

## Archivos tocados
- admisiones/services/admisiones_service/impl.py
- admisiones/templates/admisiones/admisiones_detalle.html
- admisiones/templates/admisiones/admisiones_tecnicos_form.html
- admisiones/urls/web_urls.py
- admisiones/views/web_views.py
- static/custom/js/admisionesactualizarestado.js
- comedores/models.py
- comedores/urls.py
- comedores/views/__init__.py
- comedores/views/cursos_app_mobile.py
- comedores/forms/cursos_app_mobile_form.py
- comedores/templates/comedor/cursos_app_mobile_list.html
- comedores/templates/comedor/cursos_app_mobile_form.html
- comedores/templates/comedor/cursos_app_mobile_confirm_delete.html
- comedores/migrations/0039_cursoappmobile.py
- comedores/migrations/0040_alter_cursoappmobile_managers_and_more.py
- comedores/migrations/0041_cursoappmobile_es_recomendado.py
- pwa/api_urls.py
- pwa/api_views.py
- pwa/api_serializers.py
- mobile/src/api/formacionApi.ts
- mobile/src/features/home/SpaceCursosPage.tsx
- templates/includes/sidebar/opciones.html
- templates/includes/sidebar/new_opciones.html

## Cambios realizados
- Se corrigió overflow por nombres largos en card de actividad de Nómina mobile.
- Se corrigió marcado de leído en notificaciones/mensajes mobile para que solo cambie estado local tras respuesta exitosa del backend.
- Se renombró visualmente “Cursos” a “Formación” y se cambió icono en Hub.
- Se implementó backend + ABM web de Cursos App Mobile (crear/editar/eliminar lógico, activo/inactivo, orden, imagen, programa objetivo).
- Se integró endpoint PWA de formación y consumo desde mobile.
- Se normalizó imagen de cursos a tamaño uniforme en backend y se ajustó render mobile para no romper tarjetas.
- Se agregó skeleton/loader de Formación en mobile y manejo visual de cards estilo Hub.
- Se agregó campo/check `es_recomendado` en cursos y se separó en mobile:
  - primero cursos comunes,
  - línea divisoria fina,
  - título “Cursos recomendados”,
  - luego cursos recomendados.
- En Admisiones se agregó edición de número de expediente con modal/AJAX, se alineó tooltip y se repararon acentos.
- Se dejó la edición de expediente únicamente en Técnicos (`/comedores/admisiones/tecnicos/editar/<id>`), removiéndola de otras vistas.
- En Técnicos, botón Editar y tooltip se muestran solo si ya existe número de expediente.

## Supuestos
- El endpoint de formación mantiene regla vigente: visibilidad efectiva para espacios PNUD.
- La migración `0041` se aplicará en el entorno para habilitar `es_recomendado`.

## Validaciones ejecutadas
- Revisión de consistencia con búsquedas (`rg`) para confirmar que el bloque de edición de expediente quedó solo en Técnicos.
- Revisión de consistencia de presencia de `es_recomendado` en modelo, form, serializer y mobile.
- Revisión de formato de diff (`git diff --check`) y limpieza de línea en EOF en template afectado.

## Pendientes / riesgos
- Aplicar migraciones en el entorno (`0039`, `0040`, `0041`) donde corresponda.
- Persisten algunos textos con codificación mojibake en templates históricos no relacionados directamente con este alcance.
