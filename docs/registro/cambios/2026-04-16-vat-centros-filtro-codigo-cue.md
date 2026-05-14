# VAT centros: filtro Codigo sobre CUE y limpieza de filtros

## Que cambio

- En `/vat/centros/` el filtro avanzado `Codigo` ahora busca contra el CUE vigente del centro.
- El queryset del listado prioriza el identificador historico `CUE` actual y, si no existe, usa `Centro.codigo` como fallback.
- El selector de filtros avanzados quedo reducido a `Nombre` y `Codigo`, removiendo opciones que ya no estaban alineadas con el modelo o con el flujo actual.

## Motivo

- El motor de filtros descartaba `Codigo` porque no estaba tipado en la configuracion.
- El pedido funcional requiere que el filtro represente la `Clave Unica de Establecimiento (CUE)`.
- Habia filtros visibles que ya no correspondian con atributos vigentes del modelo `Centro`, lo que generaba una UI enganosa.

## Validacion esperada

- Abrir `/vat/centros/`.
- Verificar que el modal de filtros avanzados exponga solo `Nombre` y `Codigo`.
- Aplicar un filtro por `Codigo` usando el CUE vigente de un centro y confirmar que el listado devuelve el registro correcto.
