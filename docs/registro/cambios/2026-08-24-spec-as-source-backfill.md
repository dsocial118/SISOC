# Backfill spec-as-source de flujos recientes

Fecha: 2026-08-24

## Alcance

Se consolidan en documentación canónica los contratos funcionales y
operativos detectados en la auditoría de los PRs #2288, #2300-#2301,
#2306-#2312, #2315, #2321-#2322 y #2327.

Se actualizan las guías de PWA, Usuarios/IAM, rendiciones y comandos de
administración. Se agregan guías específicas para nómina infantil SIMEPI/CDI y
altas de ciudadanos Sin DNI desde nómina. `docs/indice.md` y
`AGENT_REPO_MAP.md` quedan como puntos de entrada para esas fuentes de verdad.

## Contratos documentados

- `AccesoOrganizacionPWA` es la fuente de verdad de la membresía y sus accesos
  por comedor se reconcilian mediante signals o el comando de catch-up.
- El reset web de contraseña usa username exacto + email, respuesta genérica y
  protección frente a emails compartidos; la declaración de confidencialidad
  histórica ya no se exige en Mi cuenta.
- Rendiciones usa cinco etapas, permisos Django por etapa, filtro de estado
  compuesto, subsanaciones acumulables y un seed QA explícitamente no productivo.
- La descarga provincial SIMEPI documenta alcance, autorización, privacidad,
  deduplicación y formato PDF; la nómina de comedores documenta la excepción
  transaccional de altas Sin DNI.

## Fuentes

- `docs/implementaciones/pwa_backend.md`
- `docs/implementaciones/usuarios_perfil_iam.md`
- `docs/flujos/rendiciones_mensuales_proyectos.md`
- `docs/operacion/comandos_administracion.md`
- `docs/implementaciones/centrodeinfancia_nomina_ninos_simepi.md`
- `docs/implementaciones/comedores_nomina_ciudadanos.md`
