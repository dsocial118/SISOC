# 2026-08-31 - Informe Técnico y carátula del expediente dentro del formulario de admisiones

## Contexto
- El Informe Técnico solo podía cargarse en una página aparte
  (`informe_tecnico_form.html`), obligando al técnico a salir del formulario de
  admisiones donde carga los documentos requeridos.
- La caratulación del expediente vivía en su propio modal, con un flujo separado.
- Se pidió que el informe técnico y la carátula se completen y guarden dentro de
  la misma página `comedores/admisiones/tecnicos/editar/<pk>`
  (`admisiones_tecnicos_form.html`), con sus validaciones y campos obligatorios,
  conservando el guardado como borrador.

## Cambios aplicados
- Nuevo partial `admisiones/partials/informe_tecnico_campos.html` con todos los
  campos del Informe Técnico, extraídos sin cambios desde
  `informe_tecnico_form.html`. La página completa ahora lo incluye, así que su
  render es idéntico al anterior.
- Nuevo partial `admisiones/caratula_expediente_form.html` que muestra el número
  de expediente ya caratulado o los campos de caratulación (reutilizando
  `admisiones/partials/numero_expediente_estructurado.html`).
- `admisiones_tecnicos_form.html`: nueva sección inline `#informe-tecnico-seccion`
  (card, después de "Documentos requeridos") con un único `<form>` que combina
  carátula + informe técnico y los botones "Guardar Borrador" (`action=draft`) y
  "Finalizar" (`action=submit`). No usa modal. Los botones
  "Crear/Editar Informe Técnico" pasan a ser anclas a esa sección, y cuando
  corresponde caratular se agrega "Caratular + Informe Técnico". Si la validación
  falla, la página hace scroll a la sección con los errores.
- `AdmisionesTecnicosUpdateView`: `_add_informe_tecnico_context` arma el contexto
  de la sección (form de informe según `admision.tipo_informe`, `CaratularForm`
  con prefijo `caratula`, campos a subsanar y observación) y
  `_handle_informe_tecnico_post` procesa el POST: valida el informe, guarda
  carátula e informe dentro de una misma transacción y hace rollback si
  cualquiera de los dos falla.
- `AdmisionService.guardar_caratulacion(admision, data, prefix=None)`: nuevo
  método que concentra la validación/guardado de la caratulación.
  `_procesar_post_caratulacion` pasa a delegar en él, sin cambiar su contrato.
- Cada bloque del formulario (las 13 secciones del informe + la carátula) es
  colapsable con Bootstrap collapse: el `card-header` es el toggle y el
  `card-body` es el panel (`.collapse[data-informe-seccion]`). Arrancan
  cerrados. Nuevos assets compartidos por las dos páginas:
  `static/custom/css/informeTecnicoSecciones.css` (rotación del chevron) y
  `static/custom/js/informeTecnicoSecciones.js`, que abre las secciones con
  errores al cargar, sincroniza `aria-expanded` y despliega todo en el `click`
  del botón de envío (en fase de captura, porque un campo obligatorio oculto no
  es enfocable y el navegador cancelaría el submit sin explicar por qué).
- Corregido de paso un bug preexistente en `informe_tecnico_form.html`: usaba
  `{% block extra_js %}`, bloque que la base no declara (usa `customJS`), por lo
  que ese JS nunca se ejecutaba. El script nuevo se cargó en `customJS`; el
  bloque muerto quedó marcado con una nota, sin revivir su contenido.

## Impacto esperado
- El técnico completa carátula e informe técnico sin salir de la página de
  admisiones; el formulario se renderiza siempre que haya
  `admision.tipo_informe` y el informe no esté "Validado".
- Las páginas `informe_tecnico_crear` / `informe_tecnico_editar` y el modal
  `#caratularExpediente` (`btnCaratulacion`) siguen funcionando igual.
- Las reglas de obligatoriedad no cambian: la sección usa los mismos formularios
  y `require_full` se activa solo con `action=submit`, igual que en la página
  standalone.
- La caratulación sigue exigiendo `estado_admision = documentacion_carga_finalizada`.

## Validación
- `pytest tests/test_admisiones_web_views_unit.py tests/test_admisiones_forms_unit.py tests/test_admisiones_service_helpers_unit.py`
- `pytest -n auto -k "admision or informe"` (371 passed)
- `pytest -n auto` completo: mismos 17 fallos preexistentes que en `HEAD`
  (centrodeinfancia y `test_csv_export_architecture`), sin regresiones nuevas.
- Render manual de `admisiones_tecnicos_form.html` con y sin `num_expediente`,
  verificando la sección inline, los campos prefijados de carátula y la ausencia
  del modal.
- Chequeo estructural de los colapsables: 14 toggles emparejados 1:1 con 14
  paneles de id único, todos cerrados por defecto, sin `card-body` sin convertir;
  y render de ambas páginas confirmando que cargan el CSS y el JS.
- `black`, `pylint` (sin hallazgos nuevos) y `djlint` sobre los partials nuevos.

## Riesgos y rollback
- Riesgo principal: la sección renderiza el formulario completo del informe, por
  lo que un error en el partial afecta también a la página standalone; además la
  página de admisiones queda notablemente más larga.
- Rollback: revertir el commit; el partial es un extracto literal, así que
  volver atrás restaura el comportamiento previo sin migraciones ni datos.
