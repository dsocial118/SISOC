# Rendicion: estado visual `Subsanado` solo para archivos reemplazados

## Contexto

El detalle de rendicion podia mostrar como `Subsanado` al archivo nuevo cargado
para responder una observacion. Eso generaba ambiguedad, porque el usuario
espera ver en el archivo nuevo su estado real (`Presentado`, `Validado` o
`A Subsanar`) y reservar `Subsanado` para el documento anterior que ya fue
reemplazado.

## Cambio realizado

- El estado visual del archivo principal ahora refleja siempre su estado real.
- `Subsanado` queda reservado para los archivos historicos de la cadena que ya
  fueron reemplazados por una nueva carga.
- La regla se aplico en la construccion del detalle, por lo que impacta tanto
  en web como en los payloads de API que consumen ese armado.

## Validacion

- `docker compose exec django pytest tests/test_rendicioncuentasmensual_services_unit.py tests/test_pwa_comedores_api.py -q`
