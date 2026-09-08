# Preinscriptos CDF: listado y exportación CSV

## Alcance

Este documento define el contrato del listado de preinscriptos de Centro de
Familia en `/beneficiarios/beneficiarios/` y de su exportación CSV. Complementa
el acceso existente al padrón; no modifica quién puede ver el listado.

## Datos visibles y exportables

El listado y el CSV mantienen las mismas columnas relevantes:

- CUIL, apellido y nombre, DNI y género del beneficiario.
- Fecha de nacimiento en formato `dd/mm/aaaa`.
- Nombre y CUIL del responsable.
- Provincia, municipio y localidad.

La fecha de nacimiento y el CUIL del responsable son ordenables. La grilla
ordena sobre la página visible; el CSV aplica el orden equivalente en base de
datos, por lo que las fechas se ordenan cronológicamente aunque se muestren en
formato `dd/mm/aaaa`.

El CSV reutiliza los filtros del listado y preserva la protección contra
fórmulas de planilla de la exportación compartida. Las preferencias persistidas
de columnas prevalecen sobre las columnas visibles por defecto: quien tenga una
preferencia anterior puede habilitar las nuevas columnas desde “Configurar
columnas”.

## Acceso y datos sensibles

El acceso al listado continúa exigiendo `centrodefamilia.view_centro`. La
descarga CSV requiere uno de estos permisos:

- `auth.role_exportar_a_csv`, rol transversal de exportación.
- `auth.role_cdf_sse`, rol propio de CDF SSE.

Los permisos son alternativos solo para este exportador; conceder
`auth.role_cdf_sse` no habilita exportaciones en otros módulos. Como el archivo
incluye identificadores y fecha de nacimiento, debe tratarse como información
personal: descargarlo solo desde equipos autorizados y no compartirlo fuera del
flujo operativo CDF.

## Puntos de implementación y validación

- `centrodefamilia/views/beneficiarios_export.py` concentra columnas, orden y
  chequeo de permisos.
- `centrodefamilia/services/beneficiarios_service/impl.py` prepara las columnas
  del listado y formatea la fecha.
- `centrodefamilia/tests/test_beneficiarios_export.py` cubre CSV, orden,
  permisos y render.

Los cambios que introdujeron este contrato se registran en
`docs/registro/cambios/2026-07-27-cdf-exportacion-beneficiarios.md` y
`docs/registro/cambios/2026-07-31-cdf-beneficiarios-columnas-y-export-sse.md`.
