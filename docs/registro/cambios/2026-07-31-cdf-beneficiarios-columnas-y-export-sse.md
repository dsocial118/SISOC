# Listado de preinscriptos CDF: fecha de nacimiento, CUIL del responsable y export para CDF SSE

## Cambio

El listado de preinscriptos de Centro de Familia (`/beneficiarios/beneficiarios/`)
muestra dos columnas nuevas:

- `Fecha de nacimiento` del beneficiario, formateada `dd/mm/aaaa`.
- `CUIL del responsable`.

Ambas quedan entre las columnas existentes (fecha de nacimiento después de DNI,
CUIL del responsable después de Responsable), son ordenables y se agregan al CSV
de exportación para que el archivo siga reflejando el listado visible.

## Seguridad y permisos

La descarga del listado ahora acepta dos permisos alternativos:
`auth.role_exportar_a_csv` (rol transversal de exportación) o `auth.role_cdf_sse`.
El rol CDF SSE, que ya administra el padrón de preinscriptos, no tenía el rol
transversal y por eso no veía el botón `Descargar CSV`.

La habilitación se declara una sola vez en
`BeneficiariosExportView.export_permission_codes` y el listado la reutiliza para
decidir la visibilidad del botón, de modo que vista y template no puedan
divergir. El permiso de acceso al listado (`centrodefamilia.view_centro`) no
cambia, así que el alcance sigue acotado a quien ya puede ver preinscriptos: no
se otorga exportación a CSV en otros módulos.

## Trade-offs

- El ordenamiento por click sigue siendo client-side sobre la página visible
  (comportamiento existente de `listSort.js`): la fecha se compara como texto
  `dd/mm/aaaa`. La exportación, en cambio, replica el orden en la base con
  `SORT_FIELDS` (`fecha_nacimiento` y `responsable__cuil`), por lo que el CSV
  queda ordenado correctamente.
- Las dos columnas se agregan como visibles por defecto. Los usuarios que ya
  guardaron una preferencia de columnas para este listado deben habilitarlas
  desde "Configurar columnas", porque las preferencias persistidas mandan sobre
  los defaults.

## Validación

`centrodefamilia/tests/test_beneficiarios_export.py` cubre las columnas nuevas en
el CSV, el orden por CUIL del responsable, la descarga con rol CDF SSE, la
visibilidad del botón para ese rol y el render de las columnas en el listado.
`tests/test_beneficiarios_service_unit.py` cubre el formateo de la fecha y los
campos calculados del listado.
