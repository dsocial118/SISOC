# Reparación de mojibake capitalizado con minúsculas en identidad y PDF CDI

Fecha: 2026-09-01

## Contexto

El saneamiento productivo de la variante capitalizada reparó `Luán`, pero el
PDF provincial CDI expuso una segunda forma histórica. Ciudadano y el snapshot
de Nómina conservaban valores como `Isa\u00e3\u00adAs`,
`Nicol\u00e3\u00a1S` y `Sim\u00e3\u00b3N`, además de la frontera persistida
`ÁNabelle`.

La inspección del PDF confirmó diez casos de la variante en Buenos Aires. Una
auditoría read-only de los valores persistidos demostró que los pares
reconstruyen estrictamente `í`, `á` u `ó`; no se perdió información.

## Cambio

- La reparación acepta un par que decodifica a una minúscula sólo cuando está
  precedido por una letra y seguido por la mayúscula artificial creada por
  `str.title()`.
- Se reaplica `title()` únicamente al token afectado, preservando la
  capitalización de los demás nombres del campo.
- Una condición separada corrige tokens como `ÁNabelle` únicamente cuando
  comienzan con mayúscula latina acentuada, otra mayúscula y una minúscula.
- El comando existente y la defensa del PDF reutilizan el servicio común. No
  cambian modelos, migraciones, dependencias ni semántica RENAPER.

## Validación

- Regresiones unitarias con los patrones productivos de `Isaías`, `Simón`,
  `Tomás`, `Benjamín`, `Nicolás`, `Valentín`, `Agustín`, `Jazmín`, `Lía`,
  `León` y `Ánabelle`.
- Preservación de `João`, `São Tomé`, `Donatto Simón`, `Álvarez`, palabras
  completamente en mayúsculas y capitalización fuera del token reparado.
- Cobertura del management command para dry-run sin escrituras, `--apply` e
  idempotencia en Ciudadano y Nómina CDI.
- Cobertura de `build_export_data` sobre el snapshot CDI.

## Operación

El deploy no escribe datos. En producción, ejecutar primero:

```bash
python manage.py repair_utf8_mojibake \
  --target ciudadano \
  --target nomina_cdi \
  --batch-size 2000
```

Guardar y revisar los conteos. Sólo después de confirmar un backup consistente
y recuperable, ventana y autorización operativa:

```bash
python manage.py repair_utf8_mojibake \
  --apply \
  --target ciudadano \
  --target nomina_cdi \
  --batch-size 2000
```

Repetir el dry-run hasta obtener cero cambios reversibles y cerrar con un smoke
autenticado del PDF provincial CDI.

## Riesgos y rollback

- Los patrones ambiguos permanecen sin cambios; no se infieren tildes ausentes.
- La ejecución recorre ambas tablas y debe realizarse en una ventana de baja
  escritura.
- El rollback de datos requiere detener escrituras y restaurar el backup
  consistente de Ciudadano y Nómina CDI.

Diseño:
`docs/plans/2026-09-01-reparacion-mojibake-capitalizado-minusculas-design.md`.
