# Versionado visible por fecha en Ajustes (PWA Mobile)

## Fecha
2026-05-01

## Objetivo
Mostrar en la app mobile una referencia de versión sin gestión manual de semver, usando fecha automática de build en Ajustes.

## Alcance
Se implementó la inyección automática de fecha de build y su visualización debajo del botón `Salir` en la barra de Ajustes.

## Archivos tocados
- mobile/vite.config.ts
- mobile/src/types/app-version.d.ts
- mobile/src/ui/SettingsDrawer.tsx

## Cambios realizados
- Se reemplazó la constante de versión manual por una constante de fecha de build automática.
- Se definió `__APP_BUILD_DATE__` en tiempo de build con formato `dd.mm.yy`.
- Se actualizó la UI de Ajustes para mostrar `Actualizado: <fecha>` debajo del botón de cierre de sesión.

## Supuestos
- La fecha de build es suficiente como identificador operativo para soporte y control de despliegues.
- El formato requerido es `xx.xx.xx` interpretado como `dd.mm.yy`.

## Validaciones ejecutadas
- `npm run build` en `mobile/` (OK).
- Búsqueda de referencias para verificar consistencia de constantes:
  - `__APP_BUILD_DATE__` presente.
  - `__APP_VERSION__` removida de mobile.

## Pendientes / riesgos
- Si hay más de un despliegue en el mismo día, el valor no diferencia hora/build.
- Si se requiere granularidad mayor, puede migrarse a `dd.mm.yy HH:mm` o hash corto de commit.
