# Exportaciones CSV UTF-8 compatibles con Excel

Fecha: 2026-08-28

## Problema

Los CSV generados por distintos flujos no compartían un contrato de
codificación. En particular, `CSVExportMixin` emitía texto UTF-8 sin BOM y
Microsoft Excel podía interpretarlo como Windows-1252, aunque Google Sheets lo
leyera correctamente. Además, algunos exportadores tenían soluciones locales y
otros no declaraban el charset.

## Cambio

- Se centralizó la política en `core/services/csv_export.py`.
- Los CSV HTTP declaran `text/csv; charset=utf-8` y comienzan con un único BOM.
- `CSVExportMixin`, Auditoría, VAT, descarga de lotes de usuarios y los admins
  con `django-import-export` reutilizan el mismo contrato.
- Se retiró el BOM local de beneficiarios CDF para evitar duplicarlo.
- El fallback CSV de Celiaquía ahora escribe primero sobre texto y devuelve
  bytes `utf-8-sig`; antes intentaba usar `csv.writer` sobre `BytesIO`.

No se cambiaron columnas, delimitadores, filtros, permisos ni datos. Tampoco se
modificó la base: cualquier cambio de charset/collation en PRD requiere primero
evidencia read-only y un plan operativo separado.

## Evidencia esperada

Las pruebas cubren headers, bytes BOM, caracteres especiales y ausencia de BOM
duplicado en los caminos centrales e independientes. También existe un guard
estructural que rechaza nuevos `HttpResponse` CSV que omitan la política común.

Diseño aprobado: `docs/plans/2026-08-28-exportaciones-utf8-excel-design.md`.
