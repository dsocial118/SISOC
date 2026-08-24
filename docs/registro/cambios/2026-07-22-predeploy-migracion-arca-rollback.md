# Pre-deploy: rollback seguro de la migración ARCA

## Fecha

2026-07-22

## Contexto

La migración `organizaciones.0016_issue_2083_documentacion_organizacion`
materializa archivos ARCA en admisiones, elimina documentación histórica y
consolida documentos de avales. La reversa anterior solo restauraba parte de
los archivos y eliminaba los materializados, sin poder reconstruir el catálogo
ni las asociaciones originales.

## Decisión

La operación se declara explícitamente irreversible con
`migrations.RunPython.noop` como reversa. Así un rollback de código no realiza
una reversa parcial que pierda más información o presente un estado como
restaurado cuando no lo está.

## Consideraciones operativas

Un rollback que necesite deshacer esta migración requiere restaurar un backup
de base de datos consistente, no ejecutar solo `migrate` hacia atrás. La
promoción debe conservar el backup verificado previo a aplicar migraciones.
