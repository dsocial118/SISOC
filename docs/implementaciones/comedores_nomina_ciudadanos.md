# Comedores: alta de ciudadanos en nómina

## Alta con DNI y Sin DNI

La pantalla de alta de ciudadanos desde una nómina ofrece un único formulario
activo a la vez: con DNI o `Sin DNI`. La alternativa `Sin DNI` es exclusiva de
este flujo.

- Un ciudadano sin DNI creado desde la nómina se incorpora directamente y se
  guarda con `requiere_revision_manual=False`.
- Un alta sin DNI realizada desde otro flujo conserva la revisión manual
  obligatoria.
- El modal de incorporación de un ciudadano encontrado permite actualizar
  `pertenece_comunidad_indigena`, `en_situacion_de_calle` y
  `persona_con_celiaquia`.
- La creación/incorporación a la nómina y la actualización de esos datos se
  ejecutan en una única transacción; si falla una escritura, se revierten
  ambas.

## Implementación y pruebas

- Formulario: `comedores/forms/comedor_form.py`.
- Servicio: `comedores/services/comedor_service/impl.py`.
- Vista y template: `comedores/views/nomina.py` y
  `comedores/templates/comedor/nomina_form.html`.
- Regresiones: `tests/test_comedor_form_unit.py` y
  `tests/test_nomina_views_unit.py`.

La regla no se extiende automáticamente a altas de ciudadanos de otras
pantallas. Cualquier nuevo punto de entrada debe decidir explícitamente si
mantiene la revisión manual o adopta el contrato de nómina.

## Referencia

- `docs/registro/cambios/2026-08-10-alta-ciudadano-sin-dni-nomina.md`
