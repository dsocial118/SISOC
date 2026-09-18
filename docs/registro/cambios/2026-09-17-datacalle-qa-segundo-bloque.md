# Cambio: revisión QA de DataCalle — segundo bloque

## Alcance

Ítems del backoffice que quedaban abiertos después de la tanda del 2026-09-16
(ver `2026-09-16-datacalle-qa-alcance-provincial.md`). Los ítems de cuestionario
y de flujo observacional no entran acá: el instrumento lo regenera DATACALLE y
SISOC sólo lo copia (ver `datacalle/instrumento/README.md`).

## Comportamiento

- **QA-0020.** El cierre del relevamiento deja de estar al alcance del
  entrevistador. La API responde `403 cierre_no_autorizado` a quien no sea
  coordinador, y el backoffice gana la acción de cierre que no tenía: el
  coordinador cierra desde el detalle del operativo.
- **QA-0012.** La tarea publica `puede_iniciar`. El operativo que todavía no
  empezó sigue viajando a la app, pero marcado, así que deja de ofrecerse como
  iniciable en lugar de fallar al subir el primer caso.
- **QA-0009.** El área operativa bloquea el guardado, no sólo aparece. La tanda
  anterior le había puesto `required`, pero el formulario es `novalidate` y el
  navegador ignoraba el atributo.
- **QA-0007.** La búsqueda del listado suma al equipo: nombre, apellido,
  usuario y DNI de los integrantes.
- **QA-0015.** El alta de usuarios explica dónde se define cada rol de
  DataCalle.
- **Instrumento 2.1.0.** Se sincroniza `datacalle/instrumento/` con el contrato
  que la app publicó el 2026-09-16 (`Desktop/DataCalle-SISOC/contrato/`).
  `GET /api/datacalle/catalogos/` pasa a devolver `version: "2.1.0"`; la copia
  llevaba dos días vieja y la app comparaba contra ella.

## Decisiones

- **El endpoint de cierre se mantiene, devolviendo 403, en lugar de removerse.**
  Un 404 le llega a la app como un bug de ruteo; un 403 con código propio es una
  señal explícita de que la acción ya no le corresponde.
- **El operativo futuro no se oculta del listado de la app.** Esconderlo haría
  verdadero el ítem para el tester, pero rompería el trabajo offline: el
  entrevistador necesita bajar la tarea antes de salir a campo, donde no tiene
  conectividad. La señal (`puede_iniciar`) resuelve el problema real sin sacarle
  a la app un dato que necesita.
- **La regla de fecha vive en `puede_recibir_casos()` y la usan los dos
  caminos.** La señal que se publica y el rechazo real salen de la misma
  función, para que no puedan divergir con el tiempo.
- **No se saca el `novalidate` del formulario de planificación.** Los `select2`
  múltiples de equipo y localidades rompen la validación nativa: el navegador
  intenta enfocar un `<select>` que `select2` mantiene escondido y aborta el
  submit sin mostrar nada. La validación puntual en el submit es más chica y no
  arrastra ese riesgo. El servidor sigue siendo la fuente de verdad.
- **No se agregan coordinador ni administrador a `Profile.DataCalleRol`.** No
  son roles de la app: el coordinador y el administrador son usuarios del
  backoffice y salen del grupo `Coordinador DataCalle` y del alcance
  territorial. Sumarlos al selector habría reforzado justo la confusión que
  QA-0015 reporta. Lo que se cambió es que la pantalla lo explique.

## Pendiente

- **QA-0012 no queda cerrado del lado del tester** hasta que la app consuma
  `puede_iniciar` y deje de ofrecer el inicio. El campo es aditivo: un cliente
  que no lo lea se comporta igual que antes.
- **QA-0020 idem:** la app tiene que dejar de mostrar la acción de cierre. El
  servidor ya la rechaza, así que el agujero está cerrado, pero el relevador
  seguirá viendo el botón hasta que se publique una versión nueva.
