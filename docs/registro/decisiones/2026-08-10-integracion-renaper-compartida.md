# 2026-08-10 - Integración RENAPER compartida

## Contexto

El cliente técnico de RENAPER estaba alojado en Centro de Familia y Comedores y
Celiaquía lo importaban directamente. VAT además conservaba una copia sin
consumidores runtime detectados. La Fase 0 había introducido un puerto en
`core`, pero todavía dependía de que Centro de Familia registrara el proveedor
durante el arranque.

## Decisión

El transporte, autenticación, cache de token, timeout y clasificación de
errores viven en `core.integrations.renaper`. La fachada
`core.services.renaper` conserva el contrato compartido de consulta y su
normalización compatible. Los dominios importan únicamente esa fachada.

Se preservan el nombre de cache `renaper_token` y el TTL por defecto de 3000
segundos. No se agrega Redis: el cache sigue siendo una optimización local.

## Seguridad y operación

La integración no registra ni devuelve en errores DNI, credenciales, tokens o
payloads remotos. Los logs técnicos contienen sólo operación, tipo de error y
status HTTP cuando está disponible. Timeout y TTL se configuran con
`RENAPER_REQUEST_TIMEOUT_SECONDS` y `RENAPER_TOKEN_CACHE_TTL_SECONDS`.

## Consecuencias

- Se eliminan los clientes de Centro de Familia y VAT y el registro de
  `AppConfig.ready()`.
- No hay migraciones, cambios de permisos ni llamadas reales al servicio en
  tests.
- El rollback es revertir este cambio; no hay datos persistidos que recuperar.
