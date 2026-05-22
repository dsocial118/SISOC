# Exportación de relaciones territoriales desde fixture

## Objetivo

Generar un archivo Excel reutilizable a partir de `core/fixtures/localidad_municipio_provincia.json`
para auditar la jerarquía `provincia -> municipio -> localidad` y detectar huecos
en el fixture.

## Decisión

- Implementar un helper en `core/services/` que lea el fixture JSON y construya un
  workbook `.xlsx`.
- Exponer la generación mediante un management command de `core` para poder
  regenerar el archivo sin depender de código ad hoc.
- Generar por defecto el archivo en `out/relaciones_territoriales_fixture.xlsx`,
  porque `out/` ya está ignorado por Git.

## Validación

- Test unitario del helper verificando hojas, filas y huecos detectados.
- Test del management command verificando que genera el archivo en disco.
- Ejecución real del comando para producir el `.xlsx` solicitado.

## Supuesto explícito

Como el pedido se basa únicamente en el fixture del repo, “faltantes” se interpreta
como:

- provincias sin municipios,
- municipios sin localidades,
- municipios con provincia inexistente,
- localidades con municipio inexistente.
