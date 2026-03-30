## Celiaquía: importación de responsables en legajos

- Se ajustó `ImportacionService` para que un beneficiario menor de 18 años requiera responsable obligatoriamente durante la importación.
- Si el beneficiario es mayor de edad pero llega al menos un dato del bloque de responsable, ahora se exigen todos los campos obligatorios del responsable antes de crear legajos.
- Si el beneficiario es mayor de edad y no trae datos de responsable, la importación sigue permitiendo crear sólo el legajo del beneficiario.
- Se reutilizó `ValidacionEdadService` para mantener una única fuente de verdad sobre la regla de menores con responsable.
- Se agregaron regresiones automáticas para menor sin responsable, mayor con responsable parcial, mayor sin responsable y detección de datos parciales de responsable.
