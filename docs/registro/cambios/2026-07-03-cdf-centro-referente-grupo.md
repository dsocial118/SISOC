# CDF: campo Referente de Centro filtra por el grupo actual "CDF - Referente centro"

## Fecha
2026-07-03

## Problema
El campo `referente` en alta/edición de Centros (`/centros/nuevo/` y editar)
filtraba usuarios por el grupo legacy `ReferenteCentro`. Los usuarios del
circuito actual (generados desde el detalle del CDF o asignados por delegación)
reciben el grupo `CDF - Referente centro` (`UserGroups.CDF_REFERENTE_CENTRO`),
por lo que nunca aparecían en el desplegable ni pasaban la validación del form.

## Cambios
- `centrodefamilia/forms.py` (`CentroForm`): el queryset de `referente` ahora
  incluye `CDF - Referente centro` y conserva el legacy `ReferenteCentro` para
  no romper centros con referentes previos al renombre. Se agrega `distinct()`
  por si un usuario pertenece a ambos grupos.
- `centrodefamilia/models.py` (`Centro.referente`): mismo criterio en
  `limit_choices_to` + migración `0015_alter_centro_referente` (solo metadata,
  sin cambios de schema).
- Test de regresión: `centrodefamilia/tests/test_centro_form_referente.py`.

## Nota operativa (no código)
Para que un usuario con rol `CDF SSE` gestione usuarios desde `/usuarios/`
necesita además los permisos Django `auth.view_user`, `auth.add_user` y
`auth.change_user` (vía otro grupo/rol), más su alcance delegable
(`grupos_asignables`/`roles_asignables`) configurado. Se decidió resolverlo
asignando un rol existente con esos permisos, sin tocar el seed bootstrap.
