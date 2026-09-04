# 2026-08-13 - Queryset base de Inscripcion compartido entre reporte y buscador

## Contexto

`Inscripcion` tiene dos rutas de vinculación con centro/curso: `comision_curso`
(ComisionCurso → Curso → Centro) y `comision` (Comision → OfertaInstitucional
→ Centro). Resolver solo una de las dos rutas hace que las inscripciones de la
otra salgan con curso/centro en `NULL`, tal como ocurría en la query SQL manual
que motivó el issue de
[Buscador por Ciudadano](../../plans/2026-08-13-inet-buscador-por-ciudadano-issue.md).

`VAT/services/reportes_inscripciones_asistencia.py` ya resolvía esto
correctamente con `Coalesce` en `_base_queryset_for_user`. El Buscador por
Ciudadano necesita exactamente la misma resolución, más el alcance territorial
del usuario (`filter_centros_queryset_for_user`) y la exclusión de bajas
lógicas que esa función ya aplicaba.

## Decisión

Se extrajo `_base_queryset_for_user` tal cual a
`VAT/services/vat_inscripciones_base.py` como función pública
`base_inscripciones_queryset_for_user(user)`. El reporte y el nuevo
`VAT/services/buscador_ciudadano_service.py` la importan desde ahí; ninguno
duplica la lógica de `Coalesce`.

Durante la extracción se corrigió un `select_related` inválido heredado del
código original: `comision_curso__curso__programa` apunta a `Curso.programa`,
que es una `@property` calculada desde `voucher_parametrias`, no una FK. En el
reporte esto era inofensivo porque sus consultas siempre terminan en
`.values()`, que Django ignora junto con `select_related`; el buscador
materializa instancias de `Inscripcion` directamente, así que el
`select_related` inválido rompía con `FieldError`. Se eliminó esa entrada; no
cambia el comportamiento visible de ninguna de las dos vistas.

## Consecuencias

- Una sola fuente de verdad para la resolución de ambas rutas de inscripción:
  reduce el riesgo de que reporte y buscador diverjan a futuro.
- El reporte no cambia su comportamiento (mismos 5 tests en verde).

## Validación

- `pytest VAT/test_reporte_inscripciones_asistencia.py VAT/test_buscador_ciudadano.py -v`
