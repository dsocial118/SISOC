# Mi cuenta y confirmación obligatoria de datos personales

Fecha: 2026-08-06
Rama: `MiCuenta`

## Qué se implementó

1. Sección persistente **Mi cuenta** (`/mi-cuenta/`), accesible desde el pie del sidebar,
   donde cada usuario edita sus propios datos: nombre, apellido, DNI, CUIL, mail y
   correo institucional.
2. **Confirmación obligatoria por única vez** (`/mi-cuenta/confirmar/`): los usuarios
   existentes al momento del despliegue deben confirmar o corregir esos datos en su
   primer ingreso web posterior. Después de guardar, no se vuelve a pedir.
3. Todos los campos son obligatorios salvo **correo institucional**, más un checkbox
   de declaración que también es obligatorio.

## Cambios pedidos por UX/UI el 2026-08-06

El alcance original del ticket se modificó antes de mergear:

- **Se sacan `tipo_usuario` y `rol`** de los dos formularios. Son datos de
  administración; el usuario final no los toca. Siguen editándose desde el ABM de
  usuarios.
- **DNI y CUIL pasan a ser ambos obligatorios**, en lugar de la regla original de "al
  menos uno". La alerta general de la regla desaparece: ahora son dos errores de campo.
- **Se agrega `correo_institucional`**, único campo optativo del formulario.
- **Se agrega un checkbox de declaración obligatorio** como último campo. Arranca en
  `False` para quien nunca confirmó y el usuario debe marcarlo para poder guardar.
- **El botón Guardar datos se habilita solo con el formulario completo.**

### Texto de la declaración: pendiente

La leyenda del checkbox está en la constante `TEXTO_DECLARACION`
(`users/forms.py`), hoy con el placeholder `"TEXTO A CONFIRMAR POR UX"`. Cuando UX
envíe el texto definitivo se cambia **solo esa constante**: no hay copia duplicada en
templates ni en tests.

### El gate del botón es client-side, la validación no

`_mi_cuenta_submit_js.html` deshabilita el botón mientras `form.checkValidity()` sea
falso, apoyándose en los atributos `required` que ya renderiza Django. Es ayuda de UX:
`MiCuentaForm` valida igual del lado del servidor y hay un test que postea sin la
declaración para probarlo.

El botón se renderiza **habilitado** y el script lo deshabilita al cargar, no al revés.
Es deliberado: si el JS fallara, un botón deshabilitado por HTML dejaría al usuario sin
poder salir de un flujo que le bloquea la navegación.

## Decisiones y trade-offs

### Vista dedicada en lugar de modal embebido en el layout

El pedido original era un modal que bloquee la navegación. Un modal renderizado en el
layout no bloquea nada: se saltea navegando por URL o desde devtools. Se reutilizó el
patrón que el repo ya usa para el cambio de contraseña obligatorio
(`FirstLoginPasswordChangeMiddleware` + vista dedicada): un middleware redirige a
`/mi-cuenta/confirmar/` mientras el flag esté activo, y esa vista se presenta con
estética de modal (backdrop, sin botón de cerrar). El bloqueo es real, no visual.

### Obligatoriedad solo en el formulario, no en el modelo

Los campos siguen siendo `blank=True` en `Profile`. Varios flujos crean perfiles sin
esos datos (`services_generate_user`, provisioning automático de CDI/CDF, importación
masiva, altas desde Ticketera); hacerlos obligatorios a nivel modelo los rompería. La
obligatoriedad vive en `MiCuentaForm`.

### Formulario nuevo, no reutilización de `CustomUserChangeForm`

`CustomUserChangeForm` administra usuarios de terceros: arrastra grupos, permisos,
`roles_asignables`, alcance territorial y delegación. Reutilizarlo para autogestión
habría expuesto al usuario campos que no debe poder tocar sobre sí mismo. Se creó
`MiCuentaForm`, acotado a los campos del requerimiento, compartido entre la vista
persistente y la de confirmación para que ambas apliquen la misma validación y el mismo
guardado atómico.

### Dos middlewares encadenados

`ProfileConfirmationMiddleware` se registra **después** de
`FirstLoginPasswordChangeMiddleware` y exime `/password/first-change/`. Un usuario con
los dos flags activos primero cambia la contraseña y después confirma sus datos, sin
bucle de redirección entre ambos. Hay tests que cubren específicamente ese caso.

### Validación de formato

- CUIL: se reutiliza `core.validators.validate_cuit` (formato + dígito verificador) en
  lugar de la lógica de `ciudadanos/services_importacion_masiva.py`. Se persiste
  normalizado a 11 dígitos.
- DNI: solo se normaliza a dígitos y se exige un mínimo de 6. Se optó por ser permisivo
  a propósito: es un flujo bloqueante y una validación estricta de DNI argentino dejaría
  trabado a cualquier usuario con documento extranjero.
- **No se valida que el CUIL contenga el DNI.** Son dos campos obligatorios y
  redundantes entre sí, así que el sistema acepta que no coincidan. Si producto quiere
  esa validación cruzada, es una regla nueva en `MiCuentaForm.clean()`.

## Migración de datos

Son dos migraciones. `0045` va aparte y no plegada en `0044` porque esta última ya
había quedado aplicada en entornos de desarrollo, y editar una migración aplicada no la
vuelve a ejecutar.

`users/migrations/0044_profile_confirmacion_datos.py`:

- agrega `Profile.needs_profile_confirmation` (default `False`) y
  `Profile.datos_confirmados_at`;
- marca `needs_profile_confirmation=True` para todos los perfiles de usuarios **activos**;
- crea el perfil faltante a los usuarios activos históricos que no tenían uno (el perfil
  se crea por signal, pero hay altas viejas sin él; sin perfil el middleware los
  saltearía).

`users/migrations/0045_profile_correo_institucional_declaracion.py` agrega
`Profile.correo_institucional` y `Profile.declaracion_aceptada` (default `False`).

El default `False` de `needs_profile_confirmation` es lo que garantiza que los usuarios
creados después del despliegue no vean el flujo. Los usuarios inactivos no se marcan.

## Alcance conocido

- Los usuarios que solo operan la PWA/mobile no ven la confirmación: el middleware exime
  `/api/`. No es un bloqueo funcional, pero significa que no todo el padrón queda
  confirmado con el despliegue.
- `templates/includes/sidebar/new_opciones.html` (rediseño de sidebar todavía sin uso)
  no recibió la entrada "Mi cuenta". Cuando ese sidebar se active hay que replicarla.
- Exigir DNI **y** CUIL válidos a todo el padrón activo es un gate más duro que el del
  alcance original. Un usuario con el CUIL mal cargado no puede seguir usando el sistema
  hasta corregirlo.

## Tests

`tests/test_users_mi_cuenta.py` (28 casos): obligatoriedad campo por campo, correo
institucional optativo, declaración obligatoria, dígito verificador de CUIL,
autocompletado desde los datos en sistema, guardado atómico y limpieza del flag,
comportamiento del middleware (redirección, exenciones, prioridad frente al cambio de
contraseña), vistas, gate del botón en ambas pantallas, rechazo del guardado sin
declaración aun salteando el JS, presencia en el sidebar y lógica de la data migration.

La data migration se invoca directamente desde el test porque en el entorno de tests
(`TEST MIGRATE=False`) las data migrations no se ejecutan.

## Despliegue

Backend y UI van en el mismo release: la migración y el middleware que consume el flag
no pueden desfasarse. Conviene avisar a soporte que en el primer ingreso posterior al
deploy todos los usuarios activos verán la pantalla de confirmación.
