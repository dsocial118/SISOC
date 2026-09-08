# 2026-08-10 - Integración RENAPER compartida

## Contexto

El cliente técnico de RENAPER estaba alojado en Centro de Familia y Comedores y
Celiaquía lo importaban directamente. VAT además conservaba una copia sin
consumidores runtime detectados. La Fase 0 había introducido un puerto en
`core`, pero todavía dependía de que Centro de Familia registrara el proveedor
durante el arranque.

## Decisión

El transporte, autenticación, timeout y clasificación de
errores viven en `core.integrations.renaper`. La fachada
`core.services.renaper` conserva el contrato compartido de consulta y su
normalización compatible. Los dominios importan únicamente esa fachada.
La normalización y el caso `FALLECIDO` permanecen en la fachada como contrato
transversal heredado. Es un adaptador temporal limitado a los consumidores
existentes: no debe incorporar reglas nuevas. Se retirará cuando cada dominio
migre su mapeo e interpretación de la respuesta técnica; ese es el criterio de
salida explícito para una fase posterior, sin cambiar consumidores en esta
migración técnica.

No se persisten tokens en cache local. No se agrega Redis: cada consulta obtiene
un token efímero y evita que una credencial forme parte de estado compartido.

## Seguridad y operación

La integración no registra ni devuelve en errores DNI, credenciales, tokens o
payloads remotos. Los logs técnicos contienen sólo operación, tipo de error y
status HTTP cuando está disponible; los errores inesperados conservan un
traceback con mensaje sanitizado. El timeout se configura con
`RENAPER_REQUEST_TIMEOUT_SECONDS` y debe ser positivo.

## Consecuencias

- Se eliminan los clientes de Centro de Familia y VAT y el registro de
  `AppConfig.ready()`.
- No hay migraciones, cambios de permisos ni llamadas reales al servicio en
  tests.
- El rollback es revertir este cambio; no hay datos persistidos que recuperar.
