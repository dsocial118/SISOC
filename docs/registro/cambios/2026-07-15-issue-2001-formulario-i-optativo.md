# Issue 2001: Formulario I optativo en rendiciones PWA

## Cambio

`Formulario I - Certificación de Cuenta Bancaria` deja de ser documentación
obligatoria en la rendición de cuentas de la PWA. La categoría continúa visible
y disponible para carga, pero su ausencia ya no bloquea la presentación ni el
reenvío de una subsanación.

## Implementación

- Se actualizó la fuente central de categorías de `DocumentacionAdjunta` para
  declarar `formulario_i` como optativo.
- Se ajustaron las pruebas de presentación, detalle y reenvío para verificar el
  flujo sin un archivo de Formulario I.
- No requiere migración: la obligatoriedad es configuración de dominio y no un
  campo persistido.
