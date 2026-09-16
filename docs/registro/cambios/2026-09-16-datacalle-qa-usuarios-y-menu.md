# Cambio: revisión QA de DataCalle — usuarios y menú

## Alcance

Segundo bloque de la revisión QA del 2026-09-16 (§5.2 del canal de
coordinación): los ítems del módulo de usuarios y del menú.

## Comportamiento

- **QA-0018.** El coordinador de DataCalle ve en el listado de usuarios a los
  entrevistadores de sus provincias. Antes sólo se veía a sí mismo, así que el
  usuario que acababa de crear desaparecía.
- **QA-0016.** Al dar de alta un entrevistador, las provincias de DataCalle se
  derivan del alcance del coordinador. Con una sola provincia el campo queda
  fijo y deshabilitado, de modo que Django ignora lo que llegue por POST.
- **QA-0015.** "Tipo de usuario" y "Rol" explican qué clasifica cada uno y
  aclaran que ninguno otorga permisos; el rol de DataCalle se distingue de
  ambos en su etiqueta y su ayuda.
- **QA-0017.** Botón para ver la contraseña mientras se escribe, con estado
  accesible (`aria-pressed`) para poder dictarla al usuario nuevo.
- **QA-0014.** El coordinador que sólo trabaja en Situación de Calle ve un menú
  acotado: se le ocultan Comunicados, Configuración de Comedores y OCR.

## Decisiones

- **El alcance de usuarios se amplió con una regla propia de DataCalle, no con
  la delegación genérica.** Configurar `grupos_asignables` no servía: el
  entrevistador no se marca con un grupo sino con un flag, así que delegar
  cualquier grupo le habría mostrado al coordinador **todos los usuarios sin
  grupo del país**. La regla nueva es más angosta —relevadores de DataCalle de
  sus provincias— y es **aditiva**: no altera el alcance de ningún otro rol,
  algo que queda cubierto por tests.
- **La regla está acotada por privilegio, no sólo por provincia.** Este
  queryset no es un filtro de listado: es el `get_queryset()` de
  `UserUpdateView`, `UserDeleteView` y `UserActiveView`, o sea la guarda contra
  acceso por URL, y el formulario de usuario permite fijar contraseña. Sin un
  límite extra, alcanzaría con que un usuario del backoffice —o un
  superusuario— estuviera además marcado como relevador en la provincia para
  que un coordinador pudiera tomarle la cuenta. Por eso el universo excluye
  `is_staff` y `is_superuser`: marcar el flag de relevador fuerza
  `is_staff=False` en los dos caminos de guardado y la importación masiva no lo
  toca, así que el filtro no puede dejar afuera a un entrevistador real.
- **El camino de edición no puede quedar sin salida ni borrar de más.** Fijar
  el campo de provincias al alcance del actor choca con dos cosas: un usuario
  que todavía no es relevador no tiene provincias (el campo quedaría vacío,
  deshabilitado y con `clean` exigiendo al menos una), y un relevador puede
  tener provincias que el actor no administra (`_sync_relevador_calle_provincias`
  borra las que no lleguen). Se resuelve uniendo las provincias del perfil con
  las del alcance y ampliando el queryset del campo para que contenga esa
  unión. No abre ningún hueco porque el campo sigue `disabled`: Django ignora
  el POST y usa el initial.
- El menú reutiliza el registro de predicados que ya usaban VAT y CDI
  (`registrar_predicado_sidebar`) en lugar de sumar condiciones sueltas.
- **Usuarios, Tableros y Legajos siguen visibles** para el coordinador: ahí
  están las pantallas que necesita. Cada hijo de Legajos ya tiene su propia
  guardia de permiso, así que sólo le aparece Situación de Calle.
