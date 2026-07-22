# Issue 2133: ajustes documentales en rendiciones PWA

Fecha: 2026-07-22

## Cambios

- Se agregó el modelo descargable de `Planilla de Seguros` para la línea Tradicional.
- `Formulario III - Desagregado por Facturas SIPH` y `Formulario V - Certificación de SIPH` pasan a ser optativos para presentar una rendición.
- Ambas categorías muestran la leyenda: `Este documento es obligatorio si presentó actividades para este Convenio`.
- El catálogo offline de Mobile replica los mismos modelos, obligatoriedad y leyendas que el backend.

## Archivo

La nueva planilla se sirve desde `pwa/files/rendicion_de_cuentas`, junto con los demás modelos de rendición.
