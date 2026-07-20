# Ajustes PWA, convenios, rendiciones y documentos

## Fecha

2026-07-20

## Objetivo

Implementar los requerimientos de los issues #2085, #2084, #2083, #2081, #2063, #2036, #2096, #1990, #2001, #1901 y #1902 sobre la experiencia PWA, documentación de organizaciones, convenios, rendiciones y generación de documentos.

## Alcance

- Backend Django de Comedores, Organizaciones, Admisiones, Rendiciones Mensuales y servicios PWA.
- Interfaz PWA del repositorio anidado `mobile/`.
- Modelos y migraciones de convenio, certificaciones y documentación organizacional.
- Generación de PDF basada en plantillas DOCX y consolidación de adjuntos.
- Datos locales de prueba, sin scripts ni fixtures versionados.

## Archivos tocados

- `admisiones/services/admisiones_service/impl.py`
- `comedores/api_serializers.py`, `comedores/api_views.py`, `comedores/models.py`, `comedores/utils.py`
- `comedores/forms/convenio_pnud_form.py`, `comedores/views/comedor.py`
- `comedores/templates/comedor/comedor_convenio_pnud_form.html`, `comedores/templates/comedor/comedor_detail.html`
- `comedores/services/certificacion_prestaciones_service.py`
- `comedores/migrations/0048_issue_2063_convenio_abordaje.py`, `comedores/migrations/0049_conformidad_certificacion_pdf.py`
- `organizaciones/views.py`, `organizaciones/migrations/0016_issue_2083_documentacion_organizacion.py`
- `rendicioncuentasmensual/service_helpers.py`, `rendicioncuentasmensual/services.py`, `rendicioncuentasmensual/views.py`
- `pwa/services/nomina_destinatarios_pdf_service.py`
- `docker/django/Dockerfile`
- `pwa/files/varios/PROGRAMA.ALIMENTAR.COMUNIDAD.docx`, `pwa/files/varios/NOMINA.DE.DESTINATARIOS.docx`
- En `mobile/`: APIs de prestaciones y espacios; pantallas de organización, espacio, prestaciones, asistencia y rendiciones; reglas offline de rendición.
- `AGENT_REPO_MAP.md`

## Cambios realizados

- Se ajustó la visibilidad de espacios, prestaciones y módulos según programa y estado, manteniendo para Alimentar Comunidad únicamente espacios activos y en ejecución.
- Se adaptaron convenio y relevamiento para Abordaje Comunitario Línea Secos y Línea Tradicional, incluyendo prestaciones financiadas diarias y Merienda Reforzada donde corresponde.
- Se mantuvo la revalidación múltiple de prestaciones por período y se explicitó en la PWA.
- Se ubicó Rendiciones en el contexto de organización/programa requerido y se agregó la acción Crear Rendición con Línea Secos o Tradicional precargada.
- Se trasladó ARCA fuera del legajo organizacional, se unificó la documentación de avales y se elevó a 20 MB el límite de archivos de Organización.
- Los adjuntos de rendición aceptan hasta 20 MB en PDF, Word, Excel o formatos de imagen admitidos. Word y Excel se convierten con LibreOffice para incorporarse al PDF consolidado; ante una falla se genera una carátula de respaldo.
- Se unificó la etiqueta “Cantidad Módulos Mensuales” y se dejó optativo el Formulario I de certificación bancaria también en modo offline.
- La certificación mensual de prestaciones se genera desde `pwa/files/varios/PROGRAMA.ALIMENTAR.COMUNIDAD.docx`, se almacena y se descarga mediante un endpoint autenticado desde PWA/SISOC.
- La nómina de destinatarios se genera desde `pwa/files/varios/NOMINA.DE.DESTINATARIOS.docx` con beneficiarios activos y descarga desde la PWA.
- Se agregó LibreOffice Writer/Calc y fuentes Liberation a la imagen Django para las conversiones de documentos.

## Supuestos

- Las plantillas DOCX ubicadas en `pwa/files/varios/` son las oficiales y deben desplegarse junto con el código.
- El contenedor Django es el entorno de generación; LibreOffice debe estar disponible en runtime.
- La PWA se versiona y entrega desde su repositorio Git anidado `mobile/`.
- Las organizaciones, espacios y beneficiarios creados para prueba permanecen únicamente en la base local.

## Validaciones ejecutadas

- `black` sobre los archivos Python modificados: correcto.
- `python manage.py check`: sin observaciones.
- `python manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- `pytest comedores/tests.py pwa/tests.py rendicioncuentasmensual/tests.py organizaciones/tests.py admisiones/tests/test_admisiones_service.py -n auto`: 117 aprobadas y 3 omitidas.
- `npm run build` en `mobile/`: correcto; se mantiene la advertencia de Vite por un chunk mayor a 500 kB.
- ESLint sobre los diez archivos PWA modificados: sin errores y con dos advertencias de dependencias de hooks.
- ESLint completo de `mobile/`: no pasa por cuatro errores preexistentes fuera del alcance y advertencias de hooks.
- `git diff --check` en backend y PWA: correcto.
- `djlint --check` sobre los dos templates modificados: inconcluso; el proceso no finalizó y se cortó con timeout sin emitir errores concretos.

## Pendientes / riesgos

- Las plantillas DOCX se completan sobre posiciones estructurales del documento; cambios de diseño en las plantillas requieren revisar los servicios de generación.
- La conversión de archivos Office depende de LibreOffice y tiene un timeout de 120 segundos por documento.
- Los datos ficticios creados durante la prueba deben eliminarse manualmente si no se desean conservar en la base local.
- Quedan pendientes del baseline PWA cuatro errores del lint global en `SpaceActivitiesPage.tsx`, `ThemeContext.tsx` y `buttons.tsx`; no fueron introducidos por este lote.
- Conviene revisar por separado las dos advertencias de hooks presentes en archivos PWA modificados.
- El chequeo de templates con `djlint` debe repetirse cuando se resuelva su bloqueo sobre estos templates.
