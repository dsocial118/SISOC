# Diseño — gestión de referentes CDI por SIMEPI - EGP

## Problema

En el detalle de un Centro de Desarrollo Infantil, el rol `SIMEPI - EGP`
puede acceder al CDI dentro de su alcance territorial y editarlo, pero no ve la
última sección lateral, `Usuarios del centro`. La regla vigente limita esa
sección al propio referente asociado y al superusuario.

## Resultado esperado

- Un usuario que puede delegar `CDI - Referente centro` y tiene alcance sobre
  el CDI ve `Usuarios del centro` y los referentes asociados.
- Puede usar el alta existente mientras haya cupo.
- Puede modificar nombre, apellido, teléfono y correo del referente mediante
  la edición existente del CDI.
- No obtiene contraseñas temporales de los referentes listados.
- Fuera de su alcance territorial conserva las respuestas de acceso actuales.

## Diseño

Separar dos capacidades que hoy están acopladas:

1. Ver y gestionar los referentes asociados al CDI.
2. Ver credenciales temporales.

La primera capacidad reutiliza la delegación efectiva y el alcance territorial
que ya protegen la generación de usuarios, pero no depende del cupo restante.
Esto permite seguir viendo los referentes cuando el CDI alcanzó el límite. El
propio referente y el superusuario conservan su visibilidad actual.

La segunda capacidad se mantiene limitada al propio referente y al
superusuario. El template oculta tanto la columna como el texto de credenciales
para el gestor territorial.

No se agregan rutas, formularios, modelos ni migraciones. La edición de los
datos del referente continúa en el formulario de edición del CDI.

## Validación

- Respuesta HTTP del detalle para un gestor territorial dentro del alcance:
  muestra la sección, lista los referentes y no contiene la contraseña temporal.
- El propio referente y el superusuario mantienen el comportamiento vigente.
- La edición del CDI por EGP conserva el alcance provincial ya cubierto.
- Tests focalizados de generación/acceso CDI y validación del template.

## Riesgos y mitigaciones

- **Exposición de credenciales:** se usa un flag separado y se prueba la
  ausencia del valor sensible en la respuesta.
- **Panel oculto al completar el cupo:** la visibilidad no reutiliza la regla de
  generación, porque esa regla devuelve falso sin cupo.
- **Ampliación territorial:** se reutiliza `user_can_access_territory`; no se
  altera el queryset que limita qué CDI puede abrir EGP.
