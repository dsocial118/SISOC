# Mejoras de encuestas: portabilidad, modalidades y presentación

## Fecha

2026-09-24

## Objetivo

Resolver los puntos 1 a 4 del issue #2563: facilitar la edición, trasladar
encuestas entre ambientes, permitir no responder y unificar la presentación
con SISOC.

## Alcance

Editor, listado, segmentación, importación/exportación JSON y modal de
respuesta. Se trabajó en la rama existente por indicación del usuario.
El circuito de solicitud/aprobación de publicación (punto 5) queda fuera.

## Archivos tocados

- `encuestas/forms.py`, `models.py`, `services.py`, `views.py`, `urls.py`.
- `encuestas/migrations/0003_encuesta_opcional.py`.
- `encuestas/templates/encuestas/encuesta_form.html`, `encuesta_list.html`,
  `encuesta_segmentacion.html` y `partials/responder_modal.html`.
- `static/custom/css/encuestaForm.css`, `encuestaResponder.css`.
- `templates/components/search_bar.html` (acciones opcionales de la barra).
- `encuestas/tests/test_encuestas_portabilidad.py`, `test_encuestas_opcionales.py`.
- `docs/implementaciones/encuestas.md`, `AGENT_REPO_MAP.md`.
- `docs/tmp/encuesta-prueba.json`, `encuesta-prueba-con-segmentacion.json`,
  `encuesta-prueba-error.json`: archivos sintéticos para pruebas manuales.

## Cambios realizados

- «Agregar pregunta» al final del listado, alineado a la derecha.
- Exportación desde edición mediante menú «Solo encuesta» / «Con segmentación».
  Conserva configuración, preguntas, opciones, puntajes y condiciones.
- JSON v3, compatible al importar con v1/v2; máximo 5 MB. Importación atómica,
  sin sobrescritura: genera un borrador nuevo y vuelve al listado. La
  segmentación se conserva únicamente cuando el archivo la incluye.
- Importación con spinner, mensajes distintos según la segmentación y errores
  en rojo. Usa permisos existentes de creación/edición; no exporta respuestas.
- Modalidades obligatoria, postergable y opcional. El intervalo de recordatorio
  solo se solicita para postergables. «Prefiero no responder» descarta la ronda
  actual para ese usuario sin generar respuesta ni cumplimiento.
- Modal, editor y segmentación con paleta, tipografía y botones Poncho;
  acciones del listado compactas y separadas.
- Compatibilidad con formularios anteriores sin selector de modalidad y
  validación de longitudes/puntajes de opciones importadas antes del guardado.
- Corrección de un cierre HTML sobrante en la barra compartida y del elemento
  vacío usado para alinear acciones en segmentación, detectados por djlint.
- Migración aplicada en Docker local. Se cargó y publicó una encuesta sintética
  opcional dirigida al usuario local para revisar el modal. Son datos locales,
  no fixtures ni modificaciones a otros ambientes.

## Supuestos

- El descarte de una encuesta opcional aplica a la ronda actual; una nueva
  ronda recurrente puede volver a ofrecerse.
- Publicar sigue siendo una acción manual posterior a revisar la segmentación.
- Exportar usa lo guardado en base, no las modificaciones pendientes del editor.
- Incluir segmentación es una elección explícita que puede trasladar documentos
  personales entre ambientes, independientemente del anonimato de respuestas.

## Validaciones ejecutadas

- Migración `encuestas.0003_encuesta_opcional` aplicada en Docker local.
- `makemigrations encuestas --check --dry-run`: sin cambios pendientes.
- Black: ocho archivos Python sin diferencias de formato.
- Pylint con `pylint_django` y `.pylintrc`: 10/10 en los cinco módulos modificados.
- Djlint (`--check --lint`, `.djlintrc`): cinco templates sin errores.
- Control de encoding del repositorio aplicado al diff local y archivos nuevos:
  sin problemas UTF-8/mojibake. `git diff --check`: sin errores.
- Suite completa: `docker compose exec -T -e USE_SQLITE_FOR_TESTS=1 django pytest encuestas/tests -q --no-cov -n 4`:
  **229 pruebas aprobadas**, incluidas 49 nuevas regresiones de portabilidad y
  modalidades. Los fallos iniciales de compatibilidad del formulario quedaron
  corregidos y cubiertos en esta ejecución final.

## Pendientes / riesgos

- Aplicar la migración y reiniciar web/worker al desplegar en otros ambientes.
- La importación de JSON v3 requiere el código actualizado en el destino.
- No se incorpora aprobación de publicación (punto 5, aún en análisis).
- Revisión visual automatizada de navegador no ejecutada; la presentación se
  iteró con la revisión manual del usuario durante la sesión.
- Las pruebas usan SQLite aislado, no la base local de uso. Django emite avisos
  existentes sobre el cambio de esquema predeterminado de URLField en Django 6;
  la migración local informó la limitación de MySQL para una restricción
  condicional preexistente de `admisiones.Admision`.

Contrato funcional vigente: [Encuestas](../../implementaciones/encuestas.md).
