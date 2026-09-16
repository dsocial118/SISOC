# Convivencia de rutas de Espacios Comunitarios

Se agrega el proxy `/pwa/espacioscomunitarios/` conservando `/mobile/` y su
upstream actual. El proxy nuevo conserva el prefijo, necesario para seleccionar
el segundo build de la misma imagen de Espacios. Las otras PWA no cambian.

La dependencia de incorporacion es el Dockerfile dual del repositorio
`dsocial118/Espacios-Comunitarios`: primero imagen saludable, despues include
de Nginx. El generador sigue rechazando sustituir la base antigua de Espacios.

Validacion local: tests puros del generador y coordinador. La evidencia de build,
Nginx y despliegue se registra en el PR; este archivo no acredita por si mismo
que el cambio este instalado. El usuario delego las pruebas funcionales y de
instalacion/offline a su equipo de testers.

El 2026-09-09 se inspeccionaron los bundles de los seis contenedores existentes:
Espacios usa `/api` del origen actual, DataCalle y Gestionar usan la URL HTTPS
de SISOC correspondiente a HML/PRD. Gestionar HML conserva una constante de
respaldo de PRD, pero su `env.apiBaseUrl` compilado usa HML.

## Activacion verificada el 2026-09-09

Espacios #10 fue incorporado a main en
`7097f48930716d006fa91bad1d1547ac9094d615`. Se preparo y activo mediante el
coordinador existente, primero HML y despues PRD, y luego se instalo el include
con backup, `nginx -t` y recarga. No se promovio ni reinicio el backend.

| Entorno | Estado privado de release | Backup del include anterior |
| --- | --- | --- |
| HML | `/sisoc/SISOC/.deploy/pwa/hml.801kHkXY/state.json` | `/home/jportilla/sisoc-espacios-nginx.before-20260909T162856Z.conf` |
| PRD | `/sisoc/SISOC/.deploy/pwa/prd.5ruoqxAn/state.json` | `/home/jportilla/sisoc-espacios-nginx.before-20260909T162944Z.conf` |

Ambos estados terminaron healthy y conservan los IDs de imagen anteriores para
rollback. Los seis frontends estan saludables, con cero reinicios. Django y los
cinco workers de cada host siguen ejecutandose, con cero reinicios y las mismas
fechas de arranque previas. DataCalle y Gestionar conservan sus revisiones e
instancias anteriores.

Validacion publica en ambos dominios:

- `/mobile/` y `/pwa/espacioscomunitarios/`: HTTP 200, rutas profundas, recursos,
  manifests con ID `/mobile/` y scope/start_url propios, service workers y cache.
- Normalizacion de barra preservando query y 404 de archivos/rutas privadas
  inexistentes bajo la nueva ruta.
- DataCalle/Gestionar: rutas canonicas, aliases, assets, manifests, SW y cabeceras
  de aislamiento existentes conservados.
- API sin sesion: 401 JSON. Los bundles activos de las tres apps apuntan al
  backend de su propio entorno. Esto no acredita pruebas autenticadas.

Se retiro `/etc/sudoers.d/sisoc-pwa-temporal` en ambos servidores y se verifico
el rechazo del acceso sudo temporal al runner. Las pruebas funcionales,
instalacion/actualizacion real y sincronizacion offline quedan a los testers.
