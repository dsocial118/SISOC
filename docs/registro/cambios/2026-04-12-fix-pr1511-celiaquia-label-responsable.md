# 2026-04-12 - Fix PR 1511 Celiaquia label responsable

## Que se corrigio
- Se estabilizo el render de las etiquetas del bloque `Responsable` en el detalle de expediente de Celiaquia.
- Las labels con obligatoriedad condicional vuelven a renderizar el asterisco en la misma linea del texto, evitando falsos negativos en tests que validan el contenido HTML generado.

## Causa raiz
- Un cambio de formato en `celiaquia/templates/celiaquia/expediente_detail.html` partio labels como `Apellido Responsable *` en multiples lineas.
- El formulario seguia mostrando los campos del responsable, pero el HTML ya no contenia la cadena exacta esperada por la regresion `test_detalle_expediente_muestra_campos_responsable_para_registros_erroneos`.

## Impacto funcional
- No cambia la logica de negocio ni la validacion de responsables.
- Se recupera un HTML estable para el detalle de registros erroneos y se evita la regresion del test de render.

## Validacion
- No se pudo ejecutar `pytest` en este entorno porque Docker Desktop no estaba disponible y no hay interprete Python con dependencias del proyecto instalado en PATH.
- Se verifico la causa raiz revisando el historial del template: el commit `c3c4968f9` (`format`) introdujo el label multilinea.
