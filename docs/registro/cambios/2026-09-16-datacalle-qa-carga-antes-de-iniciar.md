# Cambio: revisión QA de DataCalle — carga de casos antes de iniciar el operativo

## Alcance

Tercer bloque de la revisión QA del 2026-09-16 (§5.2 del canal de
coordinación): la validación server-side que pidió la app (QA-0012).

## Comportamiento

- **QA-0012.** Cargar un caso en un operativo que todavía no empezó devuelve
  **409** con `codigo: "relevamiento_no_iniciado"`. La app ya lo bloquea, pero
  el servidor no puede confiar en el cliente.
- El corte sólo aplica mientras el operativo sigue en `planificado`. Una vez
  que arrancó, adelantar la fecha de inicio no vuelve a rechazar casos.
- La fecha de fin sigue sin cortar: un operativo puede estirarse.
- Las dos respuestas 409 de carga traen ahora `reintentable`.

Corrige **D2.7** del canal, que decía que las fechas eran sólo planificación.

## Decisiones

- **El estado le gana a las dos fechas, no a una sola.** La versión inicial
  cortaba por `fecha_inicio` sin mirar el estado, lo que dejaba un caso malo: si
  el coordinador corregía la fecha de inicio hacia adelante con el operativo ya
  en curso, los casos que el equipo estaba cargando empezaban a rebotar. La
  fecha de inicio ahora sólo corta mientras el operativo está `planificado`, que
  es el único escenario donde cargar es realmente un error de la app.
- **Los dos 409 se distinguen con `reintentable`.** `relevamiento_cerrado` es
  definitivo: ese caso no se va a poder subir nunca. `relevamiento_no_iniciado`
  se resuelve solo cuando arranca el operativo. Compartían forma y status, así
  que una cola offline que tratara todo 409 como "descartar" podía perder una
  jornada de campo entera. El campo es aditivo: los clientes que no lo lean
  siguen funcionando igual.

## Pendiente

`mis_relevamientos` no filtra por fecha, así que un operativo planificado a
futuro le aparece a la app como disponible. Es consistente con que el equipo
tiene que poder verlo antes de salir, pero implica que el rechazo por
`relevamiento_no_iniciado` es alcanzable en campo. Confirmar del lado de la app
que la cola offline reintenta ante `reintentable: true` en vez de descartar.
