# Reparación de mojibake en datos de identidad y PDF CDI

Fecha: 2026-09-01

## Contexto

Producción generaba la nómina provincial de niños con apellidos y nombres que
contenían secuencias equivalentes a bytes UTF-8 reinterpretados como
Windows-1252, mientras los títulos y otros textos Unicode del mismo PDF se
veían correctamente.

La inspección read-only confirmó que MySQL, la sesión y las columnas afectadas
usan `utf8mb4`. Se detectaron 198.688 ciudadanos candidatos y 26 fichas CDI;
21 de esas fichas estaban activas. La mayor concentración declaró origen
RENAPER y fecha de creación 2026.

## Cambios

- `core/integrations/renaper.py` decodifica JSON desde bytes UTF-8 estrictos,
  sin confiar en un charset HTTP incompatible, y normaliza el payload antes de
  entregarlo a consumidores.
- `core/services/text_encoding.py` repara solamente secuencias que pueden
  reconstruirse y decodificarse como UTF-8 válido. Conserva texto correcto,
  contenido mixto y casos no demostrables.
- El PDF CDI aplica la misma función como defensa para datos históricos que
  todavía no hayan sido reparados.
- `repair_utf8_mojibake` audita por defecto y sólo actualiza con `--apply` los
  campos `apellido` y `nombre` de `Ciudadano` y `NominaCentroInfancia`.
- `audit_utf8_mojibake` permite medir de forma read-only otros campos de texto
  indicados explícitamente como `app.Model.campo`.

Los comandos informan únicamente conteos. No imprimen valores, documentos ni
muestras.

## Operación

Dry-run focalizado:

```bash
python manage.py repair_utf8_mojibake \
  --target ciudadano \
  --target nomina_cdi
```

Auditoría de otros campos:

```bash
python manage.py audit_utf8_mojibake \
  --field ciudadanos.Ciudadano.apellido \
  --field ciudadanos.Ciudadano.nombre
```

La ejecución con escrituras no forma parte del despliegue ni del PR. Requiere
backup consistente, conteos de dry-run, ventana aprobada y autorización
operativa explícita:

```bash
python manage.py repair_utf8_mojibake \
  --apply \
  --target ciudadano \
  --target nomina_cdi \
  --batch-size 2000
```

Después se debe repetir el dry-run. El resultado esperado es cero filas con
cambios reversibles.

## Riesgos y rollback

- Los campos pueden mezclar caracteres correctos y rotos; por eso no se usa
  una conversión SQL de columna completa.
- Los marcadores que no forman una secuencia UTF-8 válida quedan sin cambios y
  se contabilizan para revisión.
- `--apply` bloquea sólo el lote que está actualizando y vuelve a leer las filas
  bajo `select_for_update` para no sobrescribir cambios concurrentes.
- El rollback de una ejecución productiva se realiza restaurando el backup de
  las tablas afectadas. El comando no guarda copias adicionales de PII.

Diseño: `docs/plans/2026-09-01-reparacion-mojibake-datos-design.md`.
