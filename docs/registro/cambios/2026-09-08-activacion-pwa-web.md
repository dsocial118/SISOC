# Preparacion de la activacion web de DataCalle y Gestionar

## Cambio

El usuario completo las conversiones PWA. Se habilitan ambas en el registro del
coordinador y se regenera el candidato Nginx: DataCalle en `/pwa/datacalle/`,
Gestionar en `/pwa/gestionar/`; `/mobile2/` y `/mobile3/` redirigen respectivamente
con sufijo/query. Espacios continua en `/mobile/` por su migracion pendiente.

El build incorpora `PWA_API_BASE_URL` determinista por entorno. DataCalle requiere
URL HTTPS absoluta y Gestionar debe compilar con autenticacion api, no mock.
Los archivos Compose de cada app adaptan el contrato a las variables Expo. Se
mantienen snapshots de main, gates, runtime, aislamiento y rollback existentes.

## Dependencias y riesgos

- Incorporar primero los PRs de empaquetado en main de ambas apps. El registro
  habilitado hace fallar prepare si ese contrato falta; no omite apps.
- Preparar `.env` privado en la raiz de los dos checkouts por entorno. No requiere
  secretos: SISOC inyecta las variables publicas. Los originales de la conversion
  nativa siguen apartados del build.
- DataCalle usa COOP/COEP en su contenedor para SQLite WASM/OPFS; el proxy conserva
  las cabeceras. Su API de relevamientos respondio 404 en HML y 401 JSON en PRD
  el 2026-09-08. No se cambio el backend para resolver esa diferencia.
- El permiso sudo temporal ya fue revocado: la instalacion del nuevo snippet y
  la preparacion como runner requieren restituir el acceso operativo autorizado.
- La imagen anterior permite rollback, pero sus assets no se sirven desde la
  imagen nueva. Queda pendiente probar actualizaciones con trabajo offline.
- No se ha migrado Espacios ni desplegado esta entrega en servidores.

## Validacion

- 29 tests puros de deploy_pwas, deploy_refresh, workflow y generador Nginx: pasan.
- Builds Docker reales para HML y PRD de las dos apps: pasan, con las APIs y
  subrutas correspondientes. Compilacion desde lockfile, sin .env en el contexto.
- Imagenes reales detras de Nginx 1.18 local usando el snippet generado: pasan
  health, usuario 101, filesystem read-only, navegacion SPA, aliases, manifest y
  SW con no-cache, MIME/cache de assets JS y WASM, 404 de assets inexistentes y
  rutas privadas/API del contenedor. DataCalle conserva COOP/COEP.
- Navegador local: ambas pantallas de ingreso cargan sin errores de consola.
- Gestionar emite aviso Fontconfig al compilar; el icono PNG generado fue
  inspeccionado y conserva el simbolo del producto.
- Pendientes: build/activacion en hosts, TLS/rutas publicas finales, sesion real,
  permisos, instalacion, persistencia y sincronizacion, actualizacion desde una
  version instalada. El health HTTP no acredita estos flujos.

La guia operativa y AGENT_REPO_MAP describen el orden de incorporacion y separan
la configuracion propuesta del estado efectivamente instalado.
