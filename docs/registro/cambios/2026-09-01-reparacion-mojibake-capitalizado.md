# Reparación de mojibake capitalizado en identidad y PDF CDI

Fecha: 2026-09-01

## Contexto

Después del primer saneamiento productivo, el dry-run quedó sin cambios
reversibles pero la nómina provincial CDI todavía mostró nombres con una
variante que el algoritmo original no reconocía. La inspección focalizada
confirmó el mismo valor en Ciudadano y en el snapshot de Nómina CDI.

La variante fue creada cuando un texto mojibake en mayúsculas pasó después por
`str.title()`. La transformación convirtió el marcador `Ã` en `ã` y dejó un
byte de continuación representado como carácter Unicode, por ejemplo
`Lu\u00e3\u0081N`.

## Cambio

- `core/services/text_encoding.py` reconstruye el byte inicial `C3` únicamente
  cuando `ã` y el carácter siguiente forman UTF-8 estricto y decodifican una
  letra Unicode mayúscula.
- Al confirmar ese patrón, reaplica `title()` para eliminar el límite de
  palabra artificial creado por el control histórico.
- Los flujos existentes reutilizan la corrección: defensa del PDF, auditoría
  read-only y reparación por lotes de Ciudadano y Nómina CDI.
- No cambia modelos, migraciones, integración RENAPER ni la semántica de su
  columna en el PDF.

## Validación

- Regresión unitaria del patrón productivo escapado con resultado `Luán`.
- Preservación de Unicode correcto, incluidos `João`, `São Tomé` y
  `Donatto Simón`.
- Cobertura del management command sobre Ciudadano y Nómina CDI, incluido el
  segundo dry-run idempotente.
- Cobertura de `build_export_data` para mantener el snapshot como fuente del
  PDF y entregar el nombre reparado.

## Operación

El despliegue no escribe datos. En producción:

```bash
python manage.py repair_utf8_mojibake \
  --target ciudadano \
  --target nomina_cdi \
  --batch-size 2000
```

Guardar los nuevos conteos. Como este correctivo detecta una clase antes
invisible, un resultado mayor que cero es esperable pero debe revisarse antes
de autorizar escrituras.

Después de backup consistente, ventana y autorización operativa explícita:

```bash
python manage.py repair_utf8_mojibake \
  --apply \
  --target ciudadano \
  --target nomina_cdi \
  --batch-size 2000
```

Repetir el dry-run hasta obtener cero filas con cambios reversibles y cerrar
con un smoke autenticado del PDF provincial CDI.

## Riesgos y rollback

- El patrón es deliberadamente acotado para no modificar una `ã` legítima.
- Los casos ambiguos permanecen sin cambios.
- El rollback de datos requiere detener escrituras y restaurar el backup
  consistente de las dos tablas siguiendo el procedimiento de producción.

Diseño:
`docs/plans/2026-09-01-reparacion-mojibake-capitalizado-design.md`.
