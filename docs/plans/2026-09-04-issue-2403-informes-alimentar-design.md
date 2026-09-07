# Issue 2403: Informes Técnicos y Alimentar Comunidad

## Decisiones confirmadas

- El responsable de tarjeta pertenece al legajo `Comedor`; solo el grupo `Tecnico Comedor` puede verlo o editarlo y su carga es parcial.
- Los selectores geográficos restringen nuevas cargas al catálogo, pero los campos históricos del informe permanecen como texto.
- Las precargas son solo para informes nuevos y no reemplazan datos ya guardados.
- La fuente de prestaciones es la última admisión anterior activa del mismo comedor con informe finalizado; se consideran complementarios validados.
- La exclusión de antecedentes se persiste por fila.
- Resolución de pago deja de ser visible o editable, sin borrar datos históricos.

## Alcance técnico

1. Agregar responsable de tarjeta al legajo con formulario, vista y permiso acotados.
2. Reutilizar los selectores geográficos del catálogo en Informe Técnico.
3. Precargar responsable y las 28 prestaciones en informes nuevos.
4. Incorporar criterio D y exclusión persistente de antecedentes.
5. Retirar resolución de pago de formulario, visualización y documentos nuevos.
6. Cubrir permisos, snapshots, complemento validado, antecedentes y ausencia de resolución de pago con tests focalizados.
