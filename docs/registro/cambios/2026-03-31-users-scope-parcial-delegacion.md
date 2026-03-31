# Fix de visibilidad parcial por delegación en usuarios

## Contexto

El listado de usuarios incorporó filtrado por `grupos_asignables` y
`roles_asignables` para limitar qué usuarios puede ver un delegador.

## Problema detectado

La implementación aplicaba siempre ambas comparaciones al mismo tiempo:

- subconjunto de grupos permitidos;
- subconjunto de roles directos permitidos.

Eso rompía los casos válidos donde el actor tenía configurado solo uno de los
dos ejes:

- solo grupos;
- solo roles.

En esos escenarios el listado ocultaba usuarios válidos porque trataba al eje no
configurado como si también tuviera que coincidir exactamente con vacío.

## Cambio aplicado

- Se ajustó `UsuariosService._apply_actor_scope()` para construir la condición
  final según el scope realmente presente en el perfil del actor.
- Si el actor tiene solo grupos delegables, se compara solo el subconjunto de
  grupos.
- Si el actor tiene solo roles delegables, se compara solo el subconjunto de
  roles directos.
- Si tiene ambos, se siguen exigiendo ambos.

## Validación

- Se agregaron tests de regresión en `users/tests.py` para:
  - actor con solo scope de grupos;
  - actor con solo scope de roles.
