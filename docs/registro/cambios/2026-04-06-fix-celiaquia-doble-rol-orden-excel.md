# 2026-04-06 - Fix doble rol en Celiaquia independiente del orden del Excel

## Que se corrigio

- La importacion de expedientes de Celiaquia ahora conserva el rol `beneficiario_y_responsable` aunque la persona haya aparecido primero como responsable en el Excel y recien despues como beneficiaria.
- Si durante la misma importacion una persona ya tenia un legajo `responsable` y luego aparece como beneficiaria, el legajo pendiente se promociona a `beneficiario_y_responsable` en lugar de excluirse como duplicado.
- Se agrego una consolidacion final basada en relaciones familiares efectivas del expediente para cubrir casos donde una persona es responsable de alguien y al mismo tiempo hija/beneficiaria de otra.
- Se agrego una regresion del detalle del expediente para asegurar que la familia se renderice jerarquicamente debajo del responsable real independientemente del orden de carga.

## Causa raiz

- El flujo de importacion marcaba doble rol por documento, pero al procesar la fila del beneficiario seguia usando `existentes_ids` como conflicto absoluto.
- Cuando la misma persona ya habia sido creada antes como `responsable`, su fila como beneficiaria se descartaba como "Ya existe en este expediente", por lo que nunca se procesaba la relacion con su propio responsable.
- Eso dejaba el legajo con etiqueta `responsable` y rompia la jerarquia visual esperada en expedientes con cadenas familiares.

## Impacto funcional

- El rol usado para determinar documentacion requerida ya no depende del orden de las filas en el Excel.
- Un responsable que tambien es beneficiario queda etiquetado correctamente aunque primero haya ingresado como responsable de otro.
- En el detalle del expediente, los integrantes de una misma cadena familiar se siguen mostrando debajo de su responsable correspondiente aun si el Excel vino desordenado.

## Validacion

- Se agregaron regresiones para:
  - promocion de un responsable previo a `beneficiario_y_responsable` cuando luego aparece como beneficiario,
  - consolidacion final por relaciones familiares reales,
  - orden jerarquico del detalle del expediente.
