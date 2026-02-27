# Backlog Técnico - Auditoría 2026-02-13

Estado: backlog priorizado y parcialmente ejecutado (ver cambios aplicados en CSP, entrypoint, tests y dependencias).

## Prioridad Alta

- `celiaquia/services/importacion_service.py::importar_legajos_desde_excel`
  - Problema: función monolítica (~900+ líneas).
  - Estado: varios cortes aplicados con tests unitarios (lectura/normalización del DataFrame, provincia de usuario y precarga de caches; persistencia/errores/post-procesamiento; helpers del loop para normalización/enriquecimiento de payload, creación de beneficiario, validación de conflictos/duplicados y alta de legajo beneficiario; helpers del flujo de responsable/relación; extracción de la construcción del payload por fila y de la orquestación del beneficiario create/conflict/register).
  - Pendiente: seguir reduciendo el loop principal (orquestar helpers del beneficiario/responsable en funciones de mayor nivel y extraer validaciones por fila restantes) hasta dejar el método como coordinador.

- `comedores/views/comedor.py::get_relaciones_optimizadas`
  - Problema: mezcla query-building + reglas de negocio + contexto.
  - Estado: extracción avanzada de helpers puros (nomina, actividades comunitarias, series de interacciones, celdas seguras y creator-map) y de bloques de contexto/paginación de la vista (intervenciones, observaciones, admisiones, validaciones, imágenes/programa history y `admisiones + nómina`). En esta ronda se particionó además `ComedorDetailView` (`post`, base context de relaciones, table contexts y selección de admisión/informe/prestaciones para `get_context_data`) + tests unitarios/characterization.
  - Pendiente: evaluar mover parte del assembly final de contexto a service especializado para reducir aún más acoplamiento de la vista.

- `celiaquia/views/validacion_renaper.py::_consultar_renaper`
  - Problema: flujo largo con integración externa.
  - Estado: refactor seguro aplicado con helpers de normalización/formateo/logging, retry/fallback de sexo reutilizando respuesta exitosa (sin doble llamada) y wrapper de consulta remota con retries/backoff configurables (`RENAPER_VALIDACION_MAX_RETRIES`, `RENAPER_VALIDACION_BACKOFF_SECONDS`) + tests.
  - Pendiente: encapsular cliente RENAPER/adaptador dedicado (si se decide mover completamente la integración fuera de la vista).

- `relevamientos/serializer.py::clean`
  - Problema: validación extensa en un solo método.
  - Estado: refactor incremental menor aplicado (extracción del bloque de validación de correos anidados a helper privado `_validate_contact_blocks_emails`) + tests existentes verdes.
  - Pendiente: seguir dividiendo validadores por dominio y consolidar utilidades.

- `relevamientos/service.py`, `admisiones/services/admisiones_service.py`, `admisiones/views/web_views.py`, `comedores/services/comedor_service.py`
  - Problema: módulos de baja cohesión / “god files”.
  - Estado parcial: se profundizó la partición en los cuatro módulos. `relevamientos/service.py` ya tiene extracción de helpers comunes para `populate_*`, constantes/reutilización de transformaciones y refactor de `get_relevamiento_detail_object` (prefetch/values normalizados) con tests verdes. `admisiones/services/admisiones_service.py` sumó partición de validaciones/transiciones documentales y helpers de parseo/permisos para endpoints AJAX (`numero_gde` y `convenio_numero`) con tests. `admisiones/views/web_views.py` consolidó helpers compartidos de `form_invalid`, `form_valid`, redirects y handlers `POST` en vistas de informes, más partición de `AdmisionDetailView` ya aplicada. `comedores/services/comedor_service.py` sumó partición de `get_presupuestos` en resolución de relevamiento/conteos/cálculos, manteniendo contrato + tests.
  - Acción pendiente: refactor incremental por caso de uso con pruebas antes de extraer (resta `admisiones/views/web_views.py`, `comedores/services/comedor_service.py` y más cortes en los módulos anteriores).

## Prioridad Media

- CSP estricto en `script-src` (producción)
  - Estado: middleware con `nonce` + flags (`CSP_REPORT_ONLY`, `CSP_ALLOW_UNSAFE_INLINE_SCRIPTS`, `CSP_ALLOW_UNSAFE_EVAL`) ya implementado; barrido masivo de `nonce` aplicado a scripts inline en templates + test de regresión para exigir `nonce`. También se migraron patrones repetidos y callbacks concretos a `data-*` + listeners delegados en `base.js`.
  - Estado adicional (rollback de compatibilidad): se restauró modo compatible por defecto en entornos (`CSP_ALLOW_UNSAFE_INLINE_SCRIPTS=true`), soporte legacy `onclick` en componentes genéricos y tests CSP menos estrictos para evitar conflictos en runtime. El hardening queda preparado por flags, no activado por defecto.
  - Pendiente: rollout/monitoreo en QA con `CSP_REPORT_ONLY=true` y evaluación de `CSP_ALLOW_UNSAFE_EVAL=false` si las librerías de terceros lo permiten.

- `templates/includes/base.html` y `templates/includes/new_base.html`
  - Estado: extracción de parciales compartidos (`theme_force_dark_head`, `toastr_messages`, script de dropdown theme).
  - Pendiente: converger layout canónico y mover scripts por página cuando aplique.

- `relevamientos/tasks.py`
  - Estado: resuelto en esta ejecución (guard por `PYTEST_CURRENT_TEST` y flag `DISABLE_ASYNC_THREADS`) con tests unitarios.
  - Pendiente: revisar si conviene reemplazar los threads por mecanismo de ejecución diferida más explícito (fuera de alcance actual).

## Prioridad Baja

- Revisar `FIXME` de includes (`base.html`, `new_base.html`) sobre assets/scripts potencialmente no usados.
- Documentar política final del tooling Node (se removieron `package.json`/`package-lock.json`; usar solo si se formaliza toolchain JS).

## Hallazgos ya ejecutados (resumen)

- CSP con nonce y modo report-only configurable.
- Migración de scripts inline críticos (`window.CSRF_TOKEN` y globals en templates puntuales).
- `docker/django/entrypoint.py` fail-fast (`check=True`) y flag `RUN_MAKEMIGRATIONS_ON_START`.
- Limpieza de tests fantasma/duplicados en `tests/test_clasificacion/`.
- Split de `requirements` (`base/dev/test`) con compatibilidad Docker/CI.
- Eliminación de archivo residual `celiaquia/views/comentarios_ejemplo.py`.
- Corrección del typo `related_name` de rendiciones (`archivos_adjuntos`) con compatibilidad legacy y migración.
- Refactor incremental de `validacion_renaper._consultar_renaper` (helpers + test de fallback).
- Refactor incremental de `get_relaciones_optimizadas` (helpers puros + tests).
- Corte adicional de `get_relaciones_optimizadas`: helper `_build_admisiones_y_nomina_context` + test unitario.
- Primer corte de refactor de `importar_legajos_desde_excel` (preprocesamiento/caches extraídos + tests).
- Segundo corte de refactor de `importar_legajos_desde_excel` (persistencia/errores/post-procesamiento y helpers del loop extraídos).
- Corte adicional de `importar_legajos_desde_excel`: helper de construcción de payload por fila y helper de orquestación del beneficiario + tests.
- Refactor incremental menor en `relevamientos/serializer.py::clean` (helper `_validate_contact_blocks_emails`).
- Cortes incrementales en `relevamientos/service.py::create_or_update_punto_entregas` (helpers de update/M2M) + tests.
- Corte incremental en `admisiones/services/admisiones_service.py::get_admision_update_context` (helper `_build_documentos_update_context`) + test.
- Refactor incremental en `admisiones/views/web_views.py`: helper compartido de subida de DOCX final reutilizado en dos vistas + tests de rutas felices.
- Refactor incremental en `admisiones/views/web_views.py`: `AdmisionDetailView.get_context_data` y `post` parcialmente particionados en helpers (`rendiciones`, `historial`, `dupla`, `acompañamiento`, handlers de forzar cierre/archivo adicional) + tests de fallback/rutas felices.
- Refactor incremental en `comedores/services/comedor_service.py`: helpers de resumen de nómina, builder de queryset de listado, scope por usuario y builder de queryset de detalle + tests de caracterización para coordinador, técnico/abogado, nómina y prefetch base de detalle.
- Refactor incremental en `comedores/services/comedor_service.py`: partición de `get_presupuestos` (resolución de relevamiento + conteo + cálculo) y nuevos tests para ramas sin prefetch/fallback/sin relevamientos.
- Refactor incremental en `admisiones/services/admisiones_service.py::procesar_post_update`: handlers por rama + tests de cobertura de ramas remanentes.
- Refactor incremental en `admisiones/services/admisiones_service.py`: helpers de transición documental (`verificar_estado_admision`, `_actualizar_estados_por_cambio_documento`), unificación de chequeos de obligatorios y extracción de parseo/permisos para AJAX (`actualizar_numero_gde_ajax`, `actualizar_convenio_numero_ajax`) + tests.
- Refactor incremental en `admisiones/views/web_views.py`: extracción de helpers compartidos para `form_invalid`, `form_valid` y redirects en vistas de informe técnico (`create/update/detail`) + tests unitarios de rutas `POST`.
- Refactor incremental en `comedores/views/comedor.py`: extracción de helpers de selección de admisión/informe/prestaciones y partición adicional de `ComedorDetailView` (`post`, `get_relaciones_optimizadas`, `get_context_data`) + tests.
- Refactor incremental en `relevamientos/service.py`: constantes de `prefetch`/`values` en `get_relevamiento_detail_object`, helper de normalización de listas y extracción de transformaciones reutilizables (`anexo`, `punto_entregas`, `compras`) + tests.
- Barrido de `nonce` en scripts inline + test `tests/test_templates_inline_scripts_nonce_unit.py`.
- Migración parcial de handlers inline (`history.back`, `confirm`) a `data-*` + listeners delegados en `static/custom/js/base.js`, con test de regresión.
