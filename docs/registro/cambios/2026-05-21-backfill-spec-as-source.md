# Backfill spec-as-source mayo 2026

## Contexto

La auditoria spec-as-source del 2026-05-21 detecto drift entre cambios recientes de `origin/development` y documentacion estable del repo.

## Documentacion agregada o actualizada

- Operacion de `ciudadanos_import_worker` y comando `process_ciudadanos_import_jobs`.
- Alcance territorial provincial con `ProfileTerritorialScope` en IAM.
- Formulario moderno de dispositivos.
- Transacciones Nacion Servicios desde DW en legajos de comedor.
- Documentacion organizacional versionada y reutilizacion en admisiones.
- Exportacion de nominas VAT con fallback desde observaciones.
- Indice principal de documentacion.

## Decisiones

- Los cambios se documentan como backfill sin tocar codigo.
- Las docs nuevas priorizan contratos operativos y reglas funcionales estables, no detalles de implementacion de templates.
- Los artefactos automaticos de PR/release se completan como registro historico porque el workflow no habia generado archivos recientes.

## Validacion esperada

- `git diff --check`.
- Revision manual de links y rutas documentadas.
