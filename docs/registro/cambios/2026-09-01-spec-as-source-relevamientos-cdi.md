# Consolidación documental de Relevamientos y CDI

Fecha: 2026-09-01

## Alcance

Se cierran dos huecos detectados por la auditoría spec-as-source sobre los PR
#2373 y #2380. No se modifica el comportamiento de la aplicación.

## Contratos consolidados

- Relevamientos conserva su UID territorial de AppSheet y suma la referencia
  opcional `territorial_user` a un usuario SISOC; no hay backfill de UIDs
  externos alfanuméricos. La API territorial expone esa referencia local cuando
  existe.
- `GESTIONAR_INTEGRATION_ENABLED` es el corte total y reversible de la
  integración GESTIONAR/AppSheet. Se documenta su default por ambiente, el
  parseo de valores y la necesidad de recargar el proceso que recibe el entorno.
- EGP puede operar con varias provincias completas y debe seleccionar una
  autorizada para el PDF de nómina infantil. También quedan documentadas las
  reglas CDI de formularios, nómina por edad, referentes existentes y sidebar
  de Comunicados.

## Fuentes actualizadas

- `docs/flujos/relevamiento_sync.md`
- `docs/operacion/integraciones.md`
- `docs/contexto/dominio.md`
- `docs/implementaciones/centrodeinfancia_nomina_ninos_simepi.md`
- `AGENT_REPO_MAP.md`
