# 2026-08-26 - Autorizacion por objeto en PATCH territorial PWA

## Cambio

Los PATCH de relevamiento y primer seguimiento ahora distinguen el origen de la
autorizacion:

- solicitudes autenticadas por usuario (token DRF o sesion) solo resuelven
  objetos cuyos comedores pertenecen a las provincias de
  `TerritorialComedorProvincia`;
- solicitudes por API key conservan el acceso global requerido por GESTIONAR.

Un objeto fuera de alcance se responde como `404`, igual que uno inexistente,
para no revelar su existencia. El control se hace antes de procesar serializers
o bloques relacionados.

## Cobertura

Las pruebas cubren territorial dentro y fuera de alcance, los tres
identificadores del primer seguimiento, usuarios autenticados no territoriales,
representante PWA, sesion web, y API keys moderna y legacy.
