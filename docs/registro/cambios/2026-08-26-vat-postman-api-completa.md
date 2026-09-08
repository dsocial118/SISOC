# Colección Postman completa de la API VAT

Fecha: 2026-08-26

## Objetivo

Entregar una única carpeta VAT, dentro de la colección general de SISOC, que
represente toda la superficie pública registrada por el router de VAT.

## Cambios

- Se reorganizó la carpeta VAT por dominio y superficie operativa/web.
- Se incorporaron los métodos list, retrieve, create, update, partial update y
  destroy que cada ViewSet expone.
- Se documentaron las acciones `activos`, `disponible`, `por_ciudadano`,
  `buscar`, `prioritarios`, `voucher-estado` y `prevalidar`.
- Se agregaron cuerpos de ejemplo, filtros opcionales, descripciones de
  autenticación y advertencias para operaciones de escritura.
- Los 85 requests que pueden modificar estado quedan bloqueados por un
  pre-request guard hasta
  configurar explícitamente `allowVatMutations=true`.
- `POST /api/vat/web/inscripciones/prevalidar/` queda exceptuado del guard porque
  sólo consulta y calcula elegibilidad; no persiste cambios.
- Los tests de respuesta guardan los IDs tanto en el ambiente activo como en la
  colección, para que el encadenamiento funcione al usar el ambiente Local.
- El alta web distingue entre una `Inscripcion` y una
  `SolicitudInscripcionPublica` y guarda cada ID en su variable correspondiente.
- Se completaron las variables de colección y del ambiente local para los IDs
  usados por los requests VAT.
- Se actualizó `postman/api_inventory.md` con la cobertura y los conteos reales.

## Alcance

La colección incluye `/api/vat/` y `/api/vat/web/`. No incluye vistas HTML ni
rutas AJAX internas de `VAT/urls.py`. Tampoco duplica HEAD u OPTIONS, que DRF
deriva automáticamente de las operaciones HTTP de negocio.

## Validación

- JSON válido para colección y ambiente.
- 29 registros de router analizados.
- 147 combinaciones método/ruta esperadas y 147 presentes.
- Sin combinaciones faltantes, extra o duplicadas.
- Siete acciones personalizadas representadas.
- Variables utilizadas definidas en colección o ambiente.
- Cuerpos JSON válidos luego de sustituir variables Postman.
- 85 operaciones con efectos potenciales protegidas por el guard de seguridad.
- 122 scripts de encadenamiento escribiendo en el ambiente activo y la
  colección.
- Sin rutas AJAX ni vistas HTML internas.

## Limitación contractual detectada

`POST /api/vat/vouchers/` está registrado por el `ModelViewSet`, pero no es
ejecutable con el contrato actual: `cantidad_disponible` es obligatoria en el
modelo, de solo lectura en el serializer y el ViewSet no la inicializa. La
colección conserva el request para representar fielmente la ruta expuesta, lo
marca como riesgo conocido y no afirma un resultado 201.

No se ejecutaron requests de escritura ni se probaron datos reales contra un
servidor VAT.
