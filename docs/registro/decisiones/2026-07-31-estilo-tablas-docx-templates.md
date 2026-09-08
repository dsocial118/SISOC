# Estilo base de tablas para DOCX dinámico

Fecha: 2026-07-31

## Contexto

`htmldocx` convierte correctamente la estructura de una tabla HTML, pero no
traslada el CSS que permite verla con grilla dentro del editor. El resultado
era una tabla sin bordes en Word.

## Decisión

Luego de convertir el HTML de una versión publicada, SISOC aplica el estilo
base de tabla directamente sobre OOXML: bordes, márgenes y sombreado de la
primera fila cuando corresponde a encabezados HTML.

## Consecuencias

- El aspecto del DOCX es estable sin depender de CSS editable.
- El catálogo y el sanitizado del editor no necesitan permitir estilos de
  bordes arbitrarios.
- El estilo es un estándar inicial común; futuras opciones de diseño podrán
  modelarse explícitamente si se necesitan variaciones por template.
