# 2026-03-31 - Actualización de changelog de release

## Qué cambió

- Se eliminó la versión superior `SISOC 01.04.2026` de `CHANGELOG.md`.
- Se creó una nueva versión `SISOC 31.03.2026`.
- El resumen se reconstruyó tomando como base el rango `stable-2026.03.18..origin/development`.
- Para redactar el bloque se contrastaron merges del primer parent con registros existentes en `docs/registro/cambios/` y las release notes pendientes.
- Luego se integró el avance nuevo de `origin/development` y se amplió el resumen con los cambios que todavía no estaban reflejados en el bloque superior.

## Criterio aplicado

- Se priorizó un resumen funcional por categorías (`Nuevas Funcionalidades`, `Actualizaciones`, `Corrección de Errores`) en lugar de listar todos los commits individuales.
- Se mantuvieron visibles en el texto los cambios más representativos del período: VAT, Comedores, CDI, Mobile/PWA, Celiaquía, CI y fixes de estabilidad.
- Tras el pull desde `development`, se incorporaron además los cambios recientes de VAT, delegación de usuarios y ampliaciones de nómina/CDI que habían entrado después del primer corte del changelog.
