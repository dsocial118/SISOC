# 2026-04-16 - Análisis pre-deploy development -> main

## Contexto

- Se actualizó el estado remoto del repo y se comparó `origin/main` contra `origin/development`.
- No había un PR abierto para este corte, por lo que se abrió el PR `#1564` desde la rama aislada `task/predeploy-development-main-20260416` hacia `main`.
- El delta funcional analizado corresponde al contenido de `origin/development` sobre el merge-base con `origin/main`.

## Alcance observado

- Diff agregado: `151` archivos, `9908` inserciones y `870` eliminaciones.
- Distancia entre ramas: `163` commits del lado `development` y `15` commits del lado `main` en `git rev-list --left-right --count origin/main...origin/development`.
- Módulos con mayor movimiento: `ciudadanos`, `VAT`, `celiaquia`, `acompanamientos`, `core`, `comedores`, `organizaciones` y `docs`.

## Riesgos bloqueantes

- La release incorpora la migración `acompanamientos/0007_hitos_cleanup_comedor.py`, que borra hitos huérfanos y documenta pérdida irreversible de `11` registros reales pendientes de resolución manual.
- El modelo de identidad en `ciudadanos` depende de un backfill operativo explícito (`python manage.py backfill_identidad ...`) y la propia decisión documentada exige backup y ventana coordinada antes de ejecutarlo en producción.
- No se pudo obtener señal concluyente de CI/checks sobre `origin/development` con el conector disponible, por lo que no hay evidencia automática reciente de suite verde para el commit exacto analizado.

## Riesgos no bloqueantes

- Las validaciones locales estructurales (`manage.py check` y `makemigrations --check --dry-run`) quedaron bloqueadas por la falta de `libgobject-2.0-0` al importar WeasyPrint en Windows.
- Cinco tests unitarios fallaron por la misma dependencia nativa al resolver URLs globales; no muestran una regresión funcional aislada del diff revisado.
- El corte es amplio y mezcla cambios funcionales, migraciones y tooling, por lo que el riesgo de interacción entre módulos es mayor que en un release chico.

## Validaciones ejecutadas

- `uv run --python 3.11 --with-requirements requirements.txt python -V`
- `uv run --python 3.11 --with-requirements requirements.txt python manage.py check`
- `uv run --python 3.11 --with-requirements requirements.txt python manage.py makemigrations --check --dry-run`
- `uv run --python 3.11 --with-requirements requirements.txt pytest -q tests/test_core_pagination_unit.py core/tests/test_benchmark_runner.py tests/test_context_memory_unit.py tests/test_backfill_identidad_unit.py tests/test_ciudadano_identidad_form_unit.py tests/test_ciudadano_identidad_lookup_unit.py tests/test_ciudadanos_forms_unit.py tests/test_ciudadanos_views_unit.py tests/test_importacion_service_helpers_unit.py tests/test_validacion_renaper_view_unit.py tests/test_vat_centro_form_state_unit.py tests/test_vat_centro_views_unit.py tests/test_vat_forms_unit.py tests/test_vat_persona_views_unit.py tests/test_acompanamiento_service_helpers_unit.py tests/test_acompanamientos_views_unit.py tests/test_comedor_views_unit.py tests/test_organizaciones_views_unit.py`

## Resultado

- Recomendación actual: **NO-GO** hasta completar validación en entorno Linux/Docker con WeasyPrint disponible, confirmar el tratamiento de datos borrados en `acompanamientos`, y ejecutar/planificar el backfill de identidad con backup y ventana operativa.
- Saneamiento posterior al análisis: se corrigió `.env.example`, se alineó la release note preliminar con la fecha real del corte y se cerraron observaciones puntuales de review para el release train.
