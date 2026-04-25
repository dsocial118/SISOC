# Unicidad de DNI estandar en altas desde nomina

**Fecha:** 2026-04-24

## Contexto

El modelo `Ciudadano` ya tenia `documento_unico_key` como clave unica nullable
para representar la unicidad de registros `ESTANDAR`. El hueco estaba en los
flujos de nomina: algunos caminos creaban ciudadanos directamente y no pasaban
por la normalizacion de identidad de la vista general, por lo que podian dejar
un `ESTANDAR` con `documento_unico_key=NULL`.

## Cambio

- La normalizacion de identidad queda centralizada en `Ciudadano.save()`.
- Los registros `ESTANDAR` con documento siempre guardan
  `documento_unico_key="<tipo_documento>_<documento>"`.
- Los registros `SIN_DNI` y `DNI_NO_VALIDADO_RENAPER` mantienen
  `documento_unico_key=NULL`, por lo que siguen admitiendo DNIs repetidos.
- La normalizacion no reabre revisiones manuales ya cerradas en registros
  no estandar.
- El alta desde nomina convierte el `IntegrityError` por DNI estandar duplicado
  en un mensaje de negocio controlado.

## Alcance

Este cambio solo previene nuevas altas invalidas. No sanea duplicados `ESTANDAR`
que ya pudieran existir por el hueco previo.
