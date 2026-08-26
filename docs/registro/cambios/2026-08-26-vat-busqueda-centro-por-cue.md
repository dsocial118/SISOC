# Consulta integral de Centros VAT por CUE

Fecha: 2026-08-26

## Cambio funcional

`GET /api/vat/centros/?cue=<CUE>` permite resolver un Centro por su CUE vigente
o histórico sin cambiar la ruta ni la paginación del listado. Con el parámetro
presente, la respuesta amplía la ficha con las relaciones institucionales y
formativas del Centro.

La colección Postman incluye un request de consulta y la variable `cue` en el
ambiente Local.

## Seguridad y datos excluidos

La autorización continúa siendo mediante API Key. La respuesta no incorpora
alumnos, ciudadanos, inscripciones, evaluaciones, resultados, vouchers
individuales, usuarios internos ni el documento de contactos institucionales.

## Compatibilidad

Las consultas sin `cue` conservan el serializer y el resultado anteriores. La
consulta por CUE devuelve la misma envoltura paginada y un resultado vacío para
un CUE inexistente.

## Validación

- JSON de la colección y ambiente Postman válido.
- Compilación sintáctica de los módulos Python modificados válida.
- Se añadieron tests focalizados de CUE vigente e histórico normalizado,
  compatibilidad por `Centro.codigo`, resultados duplicados paginados, error de
  formato, resultado vacío, autenticación por API key ausente o inválida y
  exclusión del documento de contacto.

La ejecución de pytest local quedó bloqueada antes de descubrir los tests:
el Python global no tiene `django-crispy-forms`, dependencia declarada por el
proyecto. No se instaló ni se levantó Docker para no modificar el entorno sin
autorización; CI ejecutará la suite en la imagen del proyecto.

## Riesgo operativo pendiente

El alcance aprobado no incorpora una migración. Antes de una carga de datos
grande conviene medir este filtro con `EXPLAIN` en la base real: la búsqueda por
`InstitucionIdentificadorHist.tipo_identificador` y
`valor_identificador` podría requerir un índice compuesto específico si el
volumen de identificadores crece.
