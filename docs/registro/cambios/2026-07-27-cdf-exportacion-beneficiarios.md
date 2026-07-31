# Exportación CSV de beneficiarios CDF

## Cambio

El listado de preinscriptos de Centro de Familia permite descargar el conjunto
filtrado en CSV UTF-8 con BOM. El botón se presenta como `Descargar CSV` en el
extremo derecho de las acciones del listado.

## Seguridad y permisos

La descarga conserva el permiso de acceso al listado
`centrodefamilia.view_centro` y exige `auth.role_exportar_a_csv`. Los valores
textuales que comienzan con caracteres de fórmula de planilla se prefijan con
una comilla simple para que Excel los trate como texto.

Actualización: desde `2026-07-31-cdf-beneficiarios-columnas-y-export-sse.md` el
rol `auth.role_cdf_sse` también habilita la descarga, como alternativa a
`auth.role_exportar_a_csv`.

## Contrato de exportación

El endpoint reutiliza los filtros del listado y acepta únicamente las columnas
ordenables visibles para replicar el orden elegido. Cuando no hay resultados,
vuelve al listado con un aviso y no genera un CSV vacío.

## Validación

Las pruebas de regresión cubren filtro, permisos, BOM, fórmulas CSV, orden por
CUIL y visibilidad del botón.
