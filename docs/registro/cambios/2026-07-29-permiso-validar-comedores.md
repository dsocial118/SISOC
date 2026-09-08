# Permiso para validar comedores (2026-07-29)

## Qué cambió

- Se incorporó el grupo bootstrap `Validador Comedores`, con el rol
  `auth.role_validador_comedores`.
- El grupo `Admin` recibe el mismo rol para conservar la capacidad de validar.
- La validación se autoriza para superusuarios, integrantes de la dupla del
  comedor o usuarios con ese rol.
- El detalle de comedor muestra los controles de validación solo a quienes
  pueden ejecutar la acción; el endpoint conserva la comprobación server-side.

## Alcance

El rol habilita solamente la acción de validar. No concede acceso de lectura ni
amplía el alcance territorial o por dupla de los comedores.

## Operación

`python manage.py create_groups` crea el grupo y sincroniza sus permisos en los
entornos donde se ejecute el arranque habitual de la aplicación.
