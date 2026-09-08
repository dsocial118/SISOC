# CDI: prevención y relevamiento de duplicados

Fecha: 2026-08-26

## Cambio funcional

- El alta de CDI exige el CUIL del referente.
- Antes de guardar un alta o edición, SISOC rechaza otro CDI activo de la misma
  provincia con la misma combinación de CUIT del organismo y CUIL del referente.
- El mensaje de validación identifica el CDI existente para que la persona
  operadora pueda corregir la carga.

## Relevamiento operativo

Se incorpora el comando de solo lectura:

```powershell
.\scripts\ai\codex_run.ps1 manage relevar_cdi_duplicados
```

El comando agrupa CDI activos con CUIT y CUIL completos, normaliza ambos
identificadores para la comparación y enmascara los valores en su salida. No
actualiza ni elimina registros.

## Límite conocido

No se agrega una restricción única de base de datos en esta entrega. Los
duplicados históricos se deben relevar y resolver primero, y la combinación
con bajas lógicas requiere una estrategia específica para MySQL antes de
imponer esa garantía a nivel de base.
