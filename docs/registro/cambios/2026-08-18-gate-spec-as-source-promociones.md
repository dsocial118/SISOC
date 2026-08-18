# Gate spec-as-source para promociones protegidas

## Cambio

`pr-docs.yml` mantiene la generación automática solo para ramas internas no
protegidas. Su verificación ahora se ejecuta también para promociones desde
`development`, `homologacion` o `main`: exige el registro de PR y el contexto
de feature ya versionados.

Cuando el destino es `main`, además exige la release note pendiente y
`CHANGELOG.md`. De ese modo una promoción no puede omitir trazabilidad porque
el bot no tenga permiso para escribir la rama protegida.

## Operación

El responsable de la promoción debe ejecutar el generador versionado, revisar
los archivos resultantes y commitearlos antes de actualizar el PR. La guía
completa está en `docs/registro/README.md`.
