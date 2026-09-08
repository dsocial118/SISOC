# Issue 2316: acceso mobile y selecciones persistentes

## Contrato confirmado

- Habilitar acceso a SISOC - Mobile es el interruptor principal de la tarjeta
  mobile, tanto para representantes como para coordinadores PWA.
- Ningún check secundario modifica ese interruptor.
- Al desactivarlo se ocultan sus opciones y se suspende el acceso efectivo.
  Los checks y alcances se conservan incluso después de guardar y volver a editar.
- El coordinador continúa siendo exclusivo de PWA y de solo lectura.

## Causa y solución

El formulario confundía el interruptor principal con el rol representante:
JavaScript desmarcaba coordinador y representante entre sí, y el servidor
rechazaba la combinación. Ahora el campo conserva el nombre interno
`es_representante_pwa` por compatibilidad con los formularios existentes, pero
el rol efectivo es coordinador cuando se selecciona esa opción bajo mobile.

`Profile.configuracion_mobile` guarda únicamente una lista explícita de checks
y alcances validados del formulario. No guarda credenciales ni concede acceso.
Al suspender mobile se desactivan los accesos con los servicios existentes y se
retiran los permisos operativos directos del formulario. Las selecciones se
recuperan de esa configuración al editar y se vuelven a validar al reactivar.
Las escrituras ocurren dentro de la transacción de guardado del usuario.

El coordinador no recibe permisos operativos, aunque estén recordados sus checks.
También se mantiene el bloqueo de login web cuando el coordinador está suspendido.
El coordinador puede asignarse o suspenderse desde el alta y la edición de un
usuario, siempre bajo el interruptor principal de acceso mobile.

La tarjeta territorial conserva su validación de incompatibilidad con los roles
representante/coordinador. Se elimina el desmarcado automático: las combinaciones
incompatibles se informan como errores de validación y nunca cambian el principal.
Los subusuarios operadores siguen administrándose desde PWA.
Los actores CDI sin gestión de mobile tampoco pueden guardar selecciones de
coordinador mediante un POST manual; se aplica a ellas la misma restricción
existente para el resto de los campos mobile.

## Migración y operación

- Migración aditiva `users.0050_profile_configuracion_mobile`, sin backfill ni
  cambios en los accesos actuales de usuarios existentes.
- Aplicar la migración antes de servir el código nuevo. El rollback del código
  puede conservar la columna; revertir también la migración elimina las
  selecciones recordadas. Los accesos suspendidos no se reactivan por un rollback.
- La configuración JSON es una preferencia del ABM, no debe usarse como prueba
  de acceso activo ni sustituir las comprobaciones de permisos de los servicios.
- Como el resto del ABM, dos ediciones concurrentes conservan la última escritura;
  este cambio no agrega control de concurrencia al formulario.

## Validación

Pruebas focalizadas: formularios, login, servicios PWA, permisos y API de comedores.
`test_mobile_selections_survive_saved_suspension` recorre alta, suspensión,
reapertura, segundo guardado y reactivación, para representante y coordinador;
comprueba permisos, credenciales, login web/mobile y uso de un token previo.

`node tests/js/user_mobile_access.test.js` ejecuta el JavaScript del template y
el controlador de visibilidad con un DOM mínimo. Recorre todos los checks de
roles/permisos del template y comprueba que no alteran el principal, además de
ocultamiento y recuperación de selecciones.

El entorno local de validación usa Python 3.12, las dependencias fijadas del repo
y SQLite temporal; Docker no estaba iniciado. No se despliega ni se valida HML
con datos reales en esta tarea. La migración necesita la validación MySQL de CI.

Resultados locales:

- 168 tests: formularios PWA, login API, flujos de autenticación, servicios PWA,
  permisos y API de comedores.
- Tras completar la protección de los campos para actores CDI, 51 tests de
  formularios PWA y agrupamiento/permisos pasaron; este conjunto se solapa con
  el anterior.
- 20 comprobaciones JavaScript pasaron.
- Chrome headless verificó el HTML renderizado de un coordinador suspendido,
  cada uno de los cinco permisos operativos, alternancia del principal y
  coordinador, y conservación de valores ocultos en `FormData`, sin errores JS.
- Black, pylint, djlint 1.43.2 y `makemigrations users --check --dry-run` pasaron.
  La comprobación local avisó que faltan bibliotecas nativas de WeasyPrint;
  no se verificó generación de PDF, que no forma parte del cambio.
