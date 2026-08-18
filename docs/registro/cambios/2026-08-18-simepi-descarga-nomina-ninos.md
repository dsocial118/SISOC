# Descarga provincial de nómina de niños SIMEPI

Fecha: 2026-08-18

## Cambio

El listado de Centros de Desarrollo Infantil incorpora la acción `Descargar
nómina de niños` para usuarios del grupo `SIMEPI - EGP`. La acción genera un
PDF con las fichas activas y únicas de la única provincia completa asignada al
perfil.

El documento:

- agrupa las filas por CDI;
- ordena por medida, edad, apellido, nombre y DNI;
- incluye los datos de identidad y la validación RENAPER solicitados;
- repite encabezados en cada página;
- agrega marca de agua, fecha, usuario y numeración total;
- termina con el total provincial;
- usa A4 apaisado y una imagen JPEG por página.

## Autorización y privacidad

El endpoint no recibe una provincia desde el cliente. Exige autenticación,
pertenencia al grupo `SIMEPI - EGP` y exactamente un alcance territorial de
provincia completa. Los demás roles, los alcances parciales y los perfiles
ambiguos reciben una denegación antes de consultar la nómina.

La respuesta usa `private, no-store`, se entrega como attachment y no persiste
el archivo en `MEDIA_ROOT`. Los errores devuelven un mensaje genérico y los
logs contienen únicamente identificadores internos y cantidades, sin DNI,
CUIL, nombres ni datos RENAPER.

## Implementación

- `centrodeinfancia/services_nomina_ninos_pdf.py` concentra consulta,
  normalización, deduplicación, render vectorial y rasterización.
- El alcance territorial se toma exclusivamente de la provincia del CDI. La
  provincia domiciliaria del niño puede estar vacía sin excluirlo.
- La deduplicación conserva la ficha activa más reciente y evita repetir tanto
  un mismo ciudadano como un mismo DNI, incluso en identidades legacy, además
  de mantener la comparación compuesta original.
- ReportLab genera el documento intermedio con Liberation Sans como alternativa
  compatible con Arial.
- `pdf2image` y Poppler convierten cada página en JPEG dentro de un directorio
  temporal.
- ReportLab crea el PDF final con una única imagen por página.

No se agregan dependencias, migraciones ni archivos persistentes. ReportLab,
Pillow, pypdf, pdf2image, Poppler y las fuentes Liberation ya forman parte del
runtime.

## Validación y rollback

La regresión focalizada cubre autorización, visibilidad del botón, filtros por
provincia del CDI y estado, inclusión con provincia domiciliaria vacía,
deduplicación por ciudadano, DNI e identidad compuesta, orden, datos RENAPER,
headers HTTP y estructura del PDF final. La inspección local de un documento
sintético de tres páginas confirmó A4 apaisado, encabezados repetidos,
legibilidad, marca de agua, pie numerado, resumen provincial y una imagen JPEG
por página sin capa de texto.

El rollback consiste en revertir la ruta, la acción de interfaz y el servicio;
no requiere reversión de esquema ni limpieza de datos.
