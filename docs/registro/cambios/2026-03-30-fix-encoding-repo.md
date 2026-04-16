# Normalización de encoding en archivos versionados

## Qué cambió

Se corrigieron cadenas con mojibake en archivos de `celiaquia`, `pwa`, `users` y tests, y se normalizaron archivos versionados que estaban en `UTF-8` con BOM para dejarlos en `UTF-8` sin BOM.

## Alcance

- Corrección de textos rotos visibles para usuarios, mensajes de error, comentarios y tests.
- Reescritura sin BOM de archivos versionados detectados en el barrido de encoding.

## Validación

- Barrido posterior sin resultados para secuencias típicas de mojibake en texto fuente.
- Barrido posterior sin resultados para archivos con BOM.
