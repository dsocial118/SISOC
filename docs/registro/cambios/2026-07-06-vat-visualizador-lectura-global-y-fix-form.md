# VAT: lectura global para INET Admin Visualizador + fixes visuales del form de centro

## Contexto (feedback de QA)

1. "En usuario admin visualizador no trae ningun dato de los centros ni permite
   visualizar ciertos puntos."
2. "Error visual en formulario de edicion de centro al final del mismo."

## Diagnostico

### Visualizador sin datos (confirmado empiricamente)

El sistema tiene dos capas: los permisos Django (`VAT.view_centro`, ...) gatean
las URLs, pero el **scope de datos** (`VAT/services/access_scope.py`) decide que
filas ve cada usuario y solo reconocia 4 identidades: SSE, provincial (perfil +
scope territorial), referente y revisor. El grupo nuevo "INET Admin
Visualizador" no era ninguna → `filter_centros_queryset_for_user()` devolvia
`.none()`: lista vacia, detalle 403, comisiones 404. Ademas carecia de
`VAT.view_curso` para el detalle de curso.

### Error visual al final del form de edicion

Dos defectos objetivos al final de `centro_create_form.html`:

- La fila de contactos sumaba **14/12 columnas** (4+3+2+2+3): el campo Email se
  desbordaba desalineado a una segunda linea. Duplicado en el loop del formset y
  en el template JS de "Agregar contacto".
- El panel "Estado de Centro" (solo en edicion) repetia la misma leyenda dos
  veces consecutivas (header del panel + cuerpo).

## Cambio

### Lectura global read-only (`access_scope.py`)

- Nuevo marcador `ROLE_VAT_ADMIN_VISUALIZADOR_PERMISSION =
  "auth.role_inet_admin_visualizador"` + helper `is_vat_admin_visualizador()`.
- Se inyecta lectura global en los 5 caminos de **lectura**:
  `filter_centros_queryset_for_user`, `can_user_access_centro`,
  `filter_ofertas_queryset_for_user`, `filter_comisiones_queryset_for_user`,
  `filter_sesiones_queryset_for_user`. Los reportes y las vistas de curso
  derivan de estas funciones, por lo que quedan cubiertos.
- Las funciones de **gestion** NO reconocen el marcador
  (`*_for_management`, `can_user_edit_centro`, `can_user_create_centro`,
  `can_user_add_vat_entities`): read-only garantizado a nivel backend, no solo
  por ocultamiento de botones.

### Seed + migracion (users/0039)

- `INET Admin Visualizador`: se agrega explicitamente el marcador
  `auth.role_inet_admin_visualizador` (antes solo lo agregaba implicitamente
  `ensure_role_for_group`; la migracion con `.set()` lo habria quitado).
- `VAT.view_curso` a los 4 perfiles VAT: `CFP`, `CFPRevisor` (solo seed,
  aditivo), `INET Admin Visualizador` e `INET Admin General`. Cierra la
  asimetria "puede editar curso pero no ver su detalle" y habilita el detalle
  read-only de curso (`vat_curso_detail`) para los perfiles de lectura.
  Resuelve el pendiente anotado en
  `2026-07-06-vat-perfiles-permisos-bootstrap.md`.

### Fixes visuales (`centro_create_form.html`)

- Grilla de contactos: 4/4/4 + 6/6 (dos filas de 12) en ambas copias del markup.
- Se elimina la leyenda duplicada del cuerpo del panel "Estado de Centro"
  (se conserva la del header, consistente con los demas paneles).

## Validacion

- `test_admin_visualizador_ve_todos_los_centros_en_solo_lectura`: lista todos
  los centros, detalle 200 con `can_edit_centro=False`, update 403.
- `test_admin_visualizador_scope_lectura_global_sin_gestion`: lectura global en
  `for_user` / `can_user_access_centro`; `for_management` vacio,
  `can_user_edit_centro` y `can_user_create_centro` False.
- `test_admin_visualizador_accede_al_detalle_de_curso_solo_lectura`: detalle de
  curso 200 sin link de edicion.
- `tests/test_create_groups_command.py` actualizado (marcador + view_curso).
- Suites: create_groups (14) + VAT centro/curso/revisor/visualizador/inet (141)
  en verde. djlint sin observaciones sobre el template.
