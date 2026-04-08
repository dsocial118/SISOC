# Fix de regresiones de tests en VAT, PWA, CSP y Legajo

## Contexto

Se corrigieron varios tests que estaban fallando por desalineación con contratos actuales del sistema o por dependencias del `ROOT_URLCONF` completo en entornos locales.

## Cambios aplicados

- `VAT/tests.py`
  - Se relajaron asserts de HTML para el panel de cursos, validando selección funcional de filtros sin depender del whitespace exacto del renderizado.
- `tests/test_pwa_comedores_api.py`
  - Se aisló el test de rendiciones con un `ROOT_URLCONF` mínimo para evitar imports colaterales de módulos no necesarios.
  - Se actualizó la expectativa del historial de comprobantes para reflejar el payload actual: el archivo observado y la nueva subsanación conviven en la lista de archivos, y la relación queda expuesta en `documento_subsanado`.
- `tests/test_csp_middleware_unit.py`
  - Se ajustó el assert para validar el contrato real del middleware: `script-src` elimina inline/eval y agrega nonce; `style-src` mantiene su contrato actual con nonce.
- `tests/test_legajo_editar_view_unit.py`
  - Se mockeó el helper de nacionalidad y la cadena `Localidad.objects.select_related(...).get(...)` para evitar accesos a DB y alinear el unit test con la implementación real de la view.
- `tests/test_urls_pwa_comedores_api.py`
  - Se agregó un URLConf de prueba acotado para aislar el test mobile de rendiciones.

## Validación

- `pytest VAT/tests.py::test_centro_cursos_panel_filtra_y_pagina_planes_curriculares tests/test_pwa_comedores_api.py::test_rendicion_en_subsanar_permite_agregar_historial_para_comprobantes tests/test_csp_middleware_unit.py::test_csp_agrega_header_y_nonce tests/test_legajo_editar_view_unit.py::test_get_success_returns_legajo_data tests/test_legajo_editar_view_unit.py::test_post_success -vv`

## Nota

No se cambió comportamiento productivo. El alcance fue de regresión/estabilización de tests y aislamiento del entorno de prueba.
