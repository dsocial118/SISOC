# IAM de infraestructura

## Objetivo

Documentar el estado informado por Infraestructura sobre accesos a servidores,
bases de datos y storage de backups para los entornos `prd`, `hml` y `qa`.

## Alcance

- Este documento registra niveles de acceso declarados, no credenciales,
  passwords ni procedimientos de provision.
- La fuente es la informacion provista por Infraestructura.
- Los terminos `usuario root`, `usuario dedicado` y `todos los permisos`
  respetan la nomenclatura recibida, sin reinterpretarla.

## Matriz de accesos

| Principal | Servidor `prd` | Servidor `hml` | Servidor `qa` | DB `prd` | DB `hml` | DB `qa` | Backups |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `jportilla`, `mfarina` | `root` + usuario dedicado con todos los permisos | `root` + usuario dedicado con todos los permisos | `root` + usuario dedicado con todos los permisos | - | - | - | Acceso a storage de backups |
| `pcao` | Usuario dedicado | Usuario dedicado | Usuario dedicado | Usuario dedicado con lectura y escritura (no root) | Usuario dedicado con lectura y escritura (no root) | Usuario dedicado con lectura y escritura (no root) | - |
| `rdolesor`, `cparra`, `jventura`, `eroyo` | - | Usuario dedicado | Usuario dedicado | Usuario dedicado con lectura y escritura | Usuario dedicado con lectura y escritura | Usuario dedicado con lectura y escritura | - |
| `datateam` | - | - | - | Usuario dedicado con permisos custom | Usuario dedicado con permisos custom | Usuario dedicado con permisos custom | - |
| `nnavarro`, `vnavarro` | - | - | Usuario dedicado | - | - | Usuario dedicado con lectura y escritura (no root) | - |
| `djangoapp` (uno por DB) | - | - | - | Usuario de aplicacion | Usuario de aplicacion | Usuario de aplicacion | - |

`-` indica que ese acceso no fue informado en el detalle recibido.

## Privilegios custom de `datateam`

Estos privilegios aplican a todas las conexiones y todos los schemas:

```text
SELECT
INSERT
UPDATE
DELETE
CREATE
DROP
REFERENCES
INDEX
ALTER
CREATE TEMPORARY TABLES
LOCK TABLES
EXECUTE
CREATE VIEW
SHOW VIEW
CREATE ROUTINE
ALTER ROUTINE
EVENT
TRIGGER
FILE
SHOW DATABASES
PROCESS
```

## Cuenta `djangoapp`

Para cada base existe una cuenta `djangoapp` con este alcance declarado:

- lectura y escritura de datos;
- creacion, alteracion y eliminacion de objetos de esquema.

## Notas operativas

- No guardar credenciales reales, hosts, strings de conexion ni secretos en este
  archivo.
- Si Infraestructura cambia altas, bajas o permisos, actualizar este documento y
  registrar el cambio en `docs/registro/cambios/`.
