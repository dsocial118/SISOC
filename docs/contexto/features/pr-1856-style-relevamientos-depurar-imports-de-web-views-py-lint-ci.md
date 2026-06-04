# Contexto de feature PR #1856 - style(relevamientos): depurar imports de web_views.py (lint CI)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1856
- Base: `main`
- Rama origen: `claude/stoic-elion-096b9c`
- Autor: `juanikitro`

## Contexto funcional

- Relevamientos — vistas web

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: chore / limpieza de imports (lint)
- Área principal declarada: relevamientos
- Impacto usuario declarado: Ninguno (sin cambios funcionales).
- Riesgos / rollback: Riesgo mínimo; revertir el commit restaura el bloque previo. No hay migraciones ni cambios de datos.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1856.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/migrations/0001_initial.py`
- `VAT/migrations/0002_remove_centro_faro_asociado_remove_centro_tipo.py`
- `VAT/migrations/0003_add_encuentro_asistencia_fechas_actividad.py`
- `VAT/migrations/0004_alter_centro_referente.py`
- `VAT/migrations/0005_remove_cabal_models.py`
- `VAT/migrations/0006_autoridadinstitucional_comision_comisionhorario_and_more.py`
- `VAT/migrations/0007_voucherparametria_voucher_parametria.py`
- `VAT/migrations/0008_voucherparametria_renovacion.py`
- `VAT/migrations/0009_voucher_asignado_por.py`
- `VAT/migrations/0010_remove_ofertainstitucional_aprobacion_inet_and_more.py`
- `VAT/migrations/0011_ofertainstitucional_costo.py`
- `VAT/migrations/0012_asistenciasesion.py`
- `VAT/migrations/0013_voucherparametria_inscripcion_unica_activa.py`
- `VAT/migrations/0014_institucionubicacion_nombre_ubicacion.py`
- `VAT/migrations/0015_institucionidentificadorhist_ubicacion.py`
- `VAT/migrations/0016_centro_campos_ubicacion_contacto_ampliado.py`
- `VAT/migrations/0017_centro_remove_legacy_fields.py`
- `VAT/migrations/0018_curso_comisioncurso.py`
- `VAT/migrations/0019_alter_comisioncurso_managers_alter_curso_managers.py`
- `VAT/migrations/0020_alter_planversioncurricular_options_and_more.py`
- ... y 368 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
