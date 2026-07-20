# 2026-07-17 - Importación de usuarios: acceso PWA y CSV de credenciales

## Cambio

- Los correos de credenciales enviados por lotes de usuarios PWA ahora indican
  la ruta `/mobile/login`; los lotes de SISOC Web mantienen el enlace habitual.
- El detalle del lote permite descargar un CSV con los usuarios efectivamente
  creados, sus datos básicos y la contraseña temporal vigente.

## Seguridad

- El CSV solo está disponible para quien creó el lote o para un superusuario.
- No persiste una nueva copia de contraseñas: si la contraseña temporal ya fue
  cambiada o reseteada, la celda se exporta vacía.
- Los valores textuales se neutralizan para evitar inyección de fórmulas al
  abrir el archivo en una planilla.
