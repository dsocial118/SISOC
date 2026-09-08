# Formato de página para templates dinámicos

Fecha: 2026-07-31

## Contexto

El editor visual ocupaba todo el ancho disponible, mientras que el DOCX se
creaba con el tamaño Letter y los márgenes predeterminados de la librería.
Eso impedía anticipar la composición final de un informe.

## Decisión

Las versiones publicadas de templates dinámicos generan un DOCX A4 vertical
con márgenes de 20 mm y estilo Normal Times New Roman de 12 pt. El editor
representa el mismo tamaño de hoja y los mismos márgenes dentro de su área de
trabajo.

## Consecuencias

- Los informes heredados conservan su generación actual.
- El editor permite anticipar ancho, márgenes y tipografía de base.
- Word puede producir diferencias menores de paginación en contenido extenso o
  tablas complejas, porque el navegador y Word usan motores de composición
  distintos.
