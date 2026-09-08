# Coleccion Postman completa de la API VAT

Fecha: 2026-08-26

## Objetivo

Actualizar la coleccion general de SISOC para que la carpeta VAT represente toda
la API publica registrada en `VAT/api_urls.py`, tanto la API operativa
`/api/vat/` como la API web `/api/vat/web/`.

## Alcance

- Incluir los metodos estandar habilitados por cada ViewSet: list, retrieve,
  create, update, partial update y destroy, segun corresponda.
- Incluir las acciones personalizadas del router VAT.
- Usar cuerpos de ejemplo alineados con los serializers y variables Postman para
  todos los identificadores reutilizables.
- Mantener descripciones de autenticacion, efectos y precondiciones, en especial
  para requests que crean, modifican o eliminan datos.
- Excluir las rutas de `VAT/urls.py`, incluidas vistas HTML y AJAX internas.

## Estructura

La carpeta VAT se organiza por superficie y recurso:

1. Informacion y autenticacion.
2. API operativa, agrupada por ubicacion, catalogos, estructura academica,
   instituciones, oferta, inscripciones, vouchers y evaluaciones.
3. API web, agrupada por centros, titulos, cursos, ciudadanos e inscripciones.

Los requests de escritura permanecen disponibles, pero un pre-request guard los
omite mientras `allowVatMutations` no se configure explícitamente en `true`.

## Validacion

- Parseo JSON de la coleccion y del ambiente.
- Inventario de metodo y ruta de todos los requests VAT.
- Cobertura de cada ruta y metodo generados por el router de DRF.
- Cobertura explicita de acciones personalizadas.
- Comprobacion de que no se incluyan rutas AJAX ni rutas HTML de `VAT/urls.py`.
- Comprobacion de variables usadas y definidas.
- Comprobacion de que todas las escrituras tengan el guard de seguridad.

## Fuera de alcance

- Cambios en endpoints, serializers, permisos o reglas de negocio.
- Ejecucion contra QA, homologacion o produccion.
- Rutas internas de la interfaz Django.
