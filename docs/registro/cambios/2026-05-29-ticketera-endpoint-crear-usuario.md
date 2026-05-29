# 2026-05-29 - Ticketera: renombre del endpoint de alta a `/auth/crear_usuario/`

## Contexto

El endpoint de alta de usuarios de la integración con la Ticketera estaba en
`POST /api/ticketera/usuarios/`. Se mueve bajo el prefijo `auth/`, junto a los
otros dos endpoints de la integración (`verificar`, `cambiar-password`), que es
donde la Ticketera espera consumir las tres operaciones.

Decisión y contratos en
[docs/registro/decisiones/2026-05-27-integracion-ticketera.md](../decisiones/2026-05-27-integracion-ticketera.md).

## Cambios aplicados

- **Endpoint:** `POST /api/ticketera/usuarios/` → `POST /api/ticketera/auth/crear_usuario/`.
- **Name de URL:** `ticketera-usuarios` → `ticketera-auth-crear-usuario`
  (`ticketera/api_urls.py`), alineado con `ticketera-auth-verificar` /
  `ticketera-auth-cambiar-password`.
- **Tests:** `ticketera/tests.py` (`reverse("ticketera-auth-crear-usuario")`) y
  `tests/test_ticketera.py` (constante `CREAR_USUARIO_URL` con la nueva ruta).
- **Docs:** ADR `2026-05-27-integracion-ticketera.md` actualizado (tabla de
  contratos, sección de contrato y referencias al endpoint) + sección datada
  con el motivo. Guía de integración externa `docs/integraciones/ticketera_api.md`.

Solo cambia la ruta y el name de URL. El método, el payload, los códigos de
respuesta (`201`/`200`/`400`/`409`/`503`) y los shapes se conservan.

## Nota de estilo

Se usa `crear_usuario` (guion bajo) por pedido explícito; el endpoint hermano
`cambiar-password` usa guion medio. Inconsistencia menor, conocida y aceptada.

## Validación

- `black --check` sobre los archivos `.py` modificados.
- `pytest ticketera/tests.py tests/test_ticketera.py` (ver nota de la corrida en
  la entrega; el grafo de migraciones heredado puede requerir `--no-migrations`).

## Rollback

Revertir la ruta y el name en `ticketera/api_urls.py` (y las referencias en
tests/docs). No hay migraciones ni cambios de modelo asociados.
