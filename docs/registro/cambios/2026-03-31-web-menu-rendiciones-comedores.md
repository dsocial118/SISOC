# Web: menú y listado global de rendiciones en Comedores

Fecha: 2026-03-31

## Qué cambió

- Se agregó la opción `Rendiciones` dentro del menú web de `Comedores`, ubicada debajo de `Acompañamiento`.
- Esa opción abre un listado global de rendiciones mensuales en web.
- Desde ese listado se puede entrar al detalle de cada rendición existente, incluidas las creadas desde Mobile.

## Implementación

- Nueva ruta web: `rendicioncuentasmensual/listado/`.
- Nueva vista: `RendicionCuentaMensualGlobalListView`.
- Nuevo template de listado global con columnas de comedor, convenio, número/período, estado y acceso al detalle.
- Se amplió el detalle web de rendición para mostrar mejor los campos incorporados por el flujo mobile:
  - comedor
  - convenio
  - número de rendición
  - período
  - estado
- El listado y el detalle se alinearon visualmente con los patrones de `Comedores`:
  - contenedor y tabla moderna de listados,
  - badges de estado con la misma familia visual,
  - presentación de detalle en cards.
- La documentación del detalle ahora se agrupa por categoría usando la misma taxonomía funcional del flujo mobile.

## Validación prevista

- `pytest tests/test_rendicioncuentasmensual_views_unit.py`
