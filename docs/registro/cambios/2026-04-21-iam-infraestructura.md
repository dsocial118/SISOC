# Registro de cambios - IAM de infraestructura

## Fecha

- 2026-04-21

## Cambio realizado

- Se agrega `docs/seguridad/iam_infraestructura.md` para registrar la matriz de
  accesos operativos informada por Infraestructura.
- Se incorpora la referencia en `docs/indice.md` para que el documento quede
  visible dentro del mapa general de seguridad.

## Alcance documentado

- Usuarios con acceso a servidores `prd`, `hml` y `qa`.
- Usuarios con acceso a bases de datos `prd`, `hml` y `qa`.
- Acceso al storage de backups.
- Privilegios custom declarados para `datateam`.
- Alcance operativo de la cuenta `djangoapp` por base.

## Fuente

- Informacion provista por Infraestructura y trasladada a documentacion sin
  incluir credenciales ni datos sensibles de conexion.
