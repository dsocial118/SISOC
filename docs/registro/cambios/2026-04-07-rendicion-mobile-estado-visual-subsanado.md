# Rendicion mobile: alineacion de estado visual con web

## Contexto

En mobile seguia activa una logica offline vieja que mostraba como `Subsanado`
al archivo nuevo cargado para responder una observacion, solo por tener
`documento_subsanado`. Eso ya se habia corregido en web y generaba
inconsistencias entre ambas interfaces.

## Cambio realizado

- La reconstruccion offline del detalle ahora toma como principal el ultimo
  archivo cargado de la cadena de subsanacion.
- El archivo principal conserva siempre su estado real (`Presentado`,
  `Validado` o `A Subsanar`).
- `Subsanado` queda reservado para los archivos historicos reemplazados dentro
  del historial de la cadena.

## Validacion

- `npm run build`
