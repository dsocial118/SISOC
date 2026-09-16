# 2026-09-16 - Destrabar los checks de CI para la promoción a producción

## Contexto

El PR #2522 (`homologacion` → `main`) tenía `black`, `djlint`, `pylint` y
`pytest` en rojo, y por arrastre `deploy_guard` quedaba bloqueado
("Checks no conformes"). Las cuatro fallas venían de la misma tanda de cambios
(el mapa vivo de arquitectura) más un template de admisiones sin formatear.

## Cambio aplicado

### Formato (sin cambio de comportamiento)

- `black` sobre `scripts/arquitectura/generar_mapa.py`,
  `core/management/commands/generar_mapa_arquitectura.py`,
  `tests/test_docker_entrypoint_unit.py` y
  `tests/test_mapa_arquitectura_generador.py`.
- `djlint` sobre `admisiones/templates/admisiones/admisiones_tecnicos_form.html`
  (solo re-indentación: el diff con `git diff -w` es vacío) y
  `core/templates/core/mapa_arquitectura.html` (`close_void_tags`).

### `docs/arquitectura/mapa_sisoc.html` queda fuera del lint

Es un **artefacto generado** por `scripts/arquitectura/generar_mapa.py --docs`.
Rompía `djlint` y el test de nonce, pero formatearlo a mano solo produce drift:
el generador lo reescribe con su propio formato en la siguiente corrida.

Se lo excluyó en `scripts/ci/pr_lint_tools.py` con un set explícito
`GENERATED_ARTIFACTS`, que es el punto por donde `black` y `djlint` eligen
archivos tanto en `pull_request` como en `push`.

### Alcance del guard de CSP (`test_all_inline_script_tags_have_nonce`)

El test recorría **todo** `*.html` del repo, incluido `docs/`. Se agregó `docs`
a `excluded_path_parts`.

Justificación: Django solo renderiza `BASE_DIR/templates` y los `templates/` de
cada app (`DIRS` + `APP_DIRS` en `config/settings.py`). Lo que vive en `docs/`
son documentos offline y mockups que ningún response sirve, así que no hay
cabecera CSP contra la cual un nonce signifique algo. El visor real del mapa
(`core/templates/core/mapa_arquitectura.html`) **sigue cubierto** por el test y
sigue usando `<script src>` externo, que es justamente lo que el CSP de
producción exige.

**Trade-off aceptado:** si alguna vez se sirviera HTML desde `docs/` por una
vista Django, este guard ya no lo cubriría. Hoy no existe ese caso.

### `pylint` R5102 en `core/views.py`

`mapa_arquitectura_datos` devuelve el grafo **ya serializado en disco**
(`grafo.read_bytes()`). Usar `JsonResponse` obligaría a parsear y volver a
serializar el archivo completo sin ningún beneficio, así que se dejó
`HttpResponse` con un `disable` puntual y su justificación en el código.

## Validación

Ejecutado con las versiones fijadas del repo (`requirements/lint.txt`,
`pylint==3.2.6`):

- `black --check .` → 1257 archivos sin cambios.
- `djlint --check` sobre la misma lista de templates del CI → `0 files would be updated`.
- `pylint core/views.py --rcfile=.pylintrc` → R5102 ya no aparece; se verificó
  contra el archivo original que el checker efectivamente dispara.
- `pytest tests/test_pr_lint_tools_unit.py tests/test_templates_inline_scripts_nonce_unit.py`
  → 4 passed (incluye un test nuevo para la exclusión de artefactos generados).
- Chequeo de mojibake sobre los 10 archivos tocados → sin hallazgos.

No se corrió la suite completa de `pytest` ni `mysql_compat` en local (requieren
el stack Docker); quedan cubiertos por el CI del PR.
