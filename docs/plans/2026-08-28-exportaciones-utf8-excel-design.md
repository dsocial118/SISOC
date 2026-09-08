# Exportaciones UTF-8 compatibles con Excel

Fecha: 2026-08-28

## Objetivo

Garantizar que toda exportación textual generada por SISOC conserve caracteres
Unicode y que los CSV descargados se abran correctamente tanto en Microsoft
Excel como en Google Sheets.

## Causa confirmada

Las exportaciones basadas en `CSVExportMixin` producen bytes UTF-8 válidos,
pero no incluyen la firma UTF-8 (BOM). Al abrir el archivo directamente, Excel
puede interpretarlo como Windows-1252 y mostrar mojibake. Google Sheets detecta
UTF-8 correctamente, lo que explica la diferencia observada.

## Contrato aprobado

- Todo CSV generado por SISOC comienza con los bytes `EF BB BF`.
- Todo response CSV declara `Content-Type: text/csv; charset=utf-8`.
- El contenido restante decodifica estrictamente como UTF-8 y conserva de forma
  exacta caracteres como `José`, `Muñoz`, `Córdoba`, `Ñandú` y `acción`.
- Se mantienen los delimitadores, columnas, filtros, permisos y nombres de
  archivo actuales.
- Los XLSX continúan siendo archivos Open XML y deben conservar Unicode al ser
  reabiertos con `openpyxl`.
- JSON y TXT descargables continúan declarando UTF-8; PDF y DOCX se validan por
  contenido visible y no mediante BOM.

## Diseño

La política CSV vive en `core` y expone constantes/utilidades pequeñas para
crear responses y anteponer el BOM. `CSVExportMixin` aplica esa política al
streaming central. Los productores independientes de Auditoría, VAT y admin
reutilizan el mismo contrato para evitar soluciones divergentes.

El workaround local de Beneficiarios CDF se elimina al quedar cubierto por el
mixin central, evitando un BOM duplicado. El fallback CSV de Celiaquía genera
primero texto y luego bytes `utf-8-sig`, porque `csv.writer` no puede escribir
cadenas sobre `BytesIO` en Python 3.

## Validación

- Pruebas de bytes, headers y contenido Unicode en el seam HTTP/archivo.
- Cobertura de `CSVExportMixin`, Auditoría, VAT y django-import-export.
- Regresión del fallback CSV de Celiaquía.
- Reapertura de un XLSX representativo con caracteres especiales.
- Guard estructural para detectar productores CSV nuevos que no adopten la
  política central.
- Validación focalizada con el runtime Docker-first del repositorio.

## Infraestructura y datos

Django ya solicita `utf8mb4` al conectarse a MySQL. La configuración efectiva
de PRD debe auditarse en modo read-only antes de proponer cambios de schema. Si
se encuentran tablas o columnas heredadas con otro charset, su conversión se
planifica por separado con backup, estimación de bloqueo y rollback; no se
mezcla con este cambio de aplicación.

## Fuera de alcance

- Cambiar delimitadores CSV o columnas exportadas.
- Modificar datos o collations de PRD sin evidencia y ventana aprobada.
- Ampliar permisos de exportación.
- Resolver CSV injection más allá de preservar las protecciones ya existentes;
  ese endurecimiento requiere una decisión de seguridad separada.
