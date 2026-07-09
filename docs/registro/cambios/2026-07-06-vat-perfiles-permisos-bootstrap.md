# VAT: perfiles de permisos administrativos (bootstrap de grupos)

## Contexto

Se ajusta la configuracion de permisos que el sistema crea al arrancar
(`manage.py create_groups`, invocado por `docker/django/entrypoint.py` tras
`migrate`). Fuente de verdad: `users/bootstrap/groups_seed.py`.

Perfiles solicitados:

- **operador CFP** → grupo existente `CFP` (sin cambios; sus permisos VAT ya
  coincidian). Se conserva el marcador de rol `auth.role_referentecentrovat`,
  necesario para que `access_scope` reconozca al usuario como referente.
- **inet provincia** → grupo existente `INET_PROVINCIA`, **redefinido** a la
  lista exacta pedida.
- **INET Admin Visualizador** → grupo **nuevo**, solo lectura VAT.
- **INET Admin General** → grupo **nuevo**, rol SSE + gestion VAT completa.

## Cambio

### `users/bootstrap/groups_seed.py`

- `INET_PROVINCIA` pasa a: `auth.role_inet_provincia`, `VAT.view_centro`,
  `VAT.add_centro`, `VAT.change_centro`, `VAT.view_planversioncurricular`,
  `VAT.add_planversioncurricular`, `VAT.view_comision`, `VAT.view_comisioncurso`.
  Se **quitan** `auth.role_provincia_vat`, `VAT.change_planversioncurricular`,
  `VAT.view_ofertainstitucional`, `VAT.change_ofertainstitucional`,
  `VAT.change_comision`. Consecuencia buscada: INET_PROVINCIA ya **no edita**
  planes / ofertas / comisiones (solo crea planes/centros y visualiza
  comisiones). La feature de "edicion parcial con campos bloqueados" para ese
  perfil queda dormida.
- Nuevo grupo **`INET Admin Visualizador`**: `VAT.view_centro`,
  `VAT.view_comision`, `VAT.view_comisioncurso`, `VAT.view_comisionhorario`,
  `VAT.view_inscripcion`, `VAT.view_inscripcionoferta`,
  `VAT.view_planversioncurricular`.
- Nuevo grupo **`INET Admin General`**: `auth.role_vat_sse`,
  `auth.role_admin_inet_general` + gestion VAT completa (centro, curso,
  comision, comisioncurso, comisionhorario, inscripcion, asistenciasesion,
  planversioncurricular segun la lista pedida).

`create_groups` es aditivo y crea on-demand los `auth.role_*` faltantes (p. ej.
`role_admin_inet_general`). Ademas `ensure_role_for_group` agrega a cada grupo su
rol homonimo (`role_cfp`, `role_inet_admin_visualizador`,
`role_inet_admin_general`) — comportamiento preexistente del sistema.

### Migracion `users/0039_reconcile_vat_admin_groups.py`

`create_groups` no **quita** permisos en entornos ya existentes. Se agrega una
data migration que deja los 4 grupos (`CFP`, `INET_PROVINCIA`,
`INET Admin Visualizador`, `INET Admin General`) con EXACTAMENTE los permisos
del seed via `permissions.set(...)`, removiendo los sobrantes (los 5 permisos
retirados de INET_PROVINCIA). Crea on-demand los `auth.role_*` inexistentes.

## Validacion

- `tests/test_create_groups_command.py`: se actualizo el test de INET_PROVINCIA
  a la nueva lista (y a la ausencia de los permisos retirados) y se agregaron
  tests para `INET Admin Visualizador`, `INET Admin General` y para la migracion
  de reconciliacion (quita permisos stale y crea `role_admin_inet_general`).
- `VAT/tests.py`: los 5 tests de "edicion parcial INET_PROVINCIA" pasan a
  afirmar el **bloqueo (403)** de plan/oferta/comision update; los dos de GET se
  renombraron a `..._no_puede_acceder_a_...`.
- Suites `create_groups` + VAT inet/provincia + group/permission/seed: verdes.

## Nota / pendiente

Ninguno de los 4 grupos incluye `VAT.view_curso`, permiso que gatea el detalle
de curso en solo lectura (boton "Ver" + `vat_curso_detail`) agregado en
`2026-07-06-vat-curso-detalle-solo-lectura.md`. Con esta config, ese detalle no
es alcanzable por estos perfiles (ni por `CFPRevisor`). Si se quiere habilitar
la visualizacion de curso para los perfiles de solo lectura, hay que agregar
`VAT.view_curso` a los grupos correspondientes o re-gatear el boton sobre un
permiso que ya posean (p. ej. `VAT.view_comisioncurso`).
