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
- El permiso sudo temporal fue restituido por el usuario y verificado en HML/PRD.
  Queda pendiente retirarlo al completar la instalacion o cerrar la intervencion.
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
- Pendientes: activacion en hosts, TLS/rutas publicas finales, sesion real,
  permisos, instalacion, persistencia y sincronizacion, actualizacion desde una
  version instalada. El health HTTP no acredita estos flujos.

La guia operativa y AGENT_REPO_MAP describen el orden de incorporacion y separan
la configuracion propuesta del estado efectivamente instalado.

## Preparacion de servidores tras restablecer acceso

- Acceso SSH como operador y sudo como sisoc-deploy: verificados en ambos hosts.
- Creados `/sisoc/DataCalle/.env` y `/sisoc/Gestionar/.env` en HML/PRD, con modo
  600 y propietario sisoc-deploy. Solo contienen un comentario; los originales
  privados permanecen apartados. No se sobrescribio ningun archivo existente.
- Fetch main y comprobacion de ancestro/checkouts sin cambios tracked: pasan.
  Gestionar main `df4bce1a267e486326a2d3dd068268d7b618f8f0` incluye Compose;
  DataCalle main `6a41b1bf81c9d580510f48aac2e8712d52d9663a` todavia no lo incluye.
- HML: 2,6 GB libres, 98% de uso; Docker informa 9,896 GB de cache recuperable.
  PRD: 578 GB libres, 24% de uso. No se iniciaron builds con ese margen en HML.
  No se eliminaron caches, imagenes ni volumenes.
- Revalidacion publica de DataCalle: API HML 404 HTML, PRD 401 JSON.
- No hubo activacion de contenedores ni cambios/reloads de Nginx.

## Builds en servidores despues de recuperar espacio

El usuario recupero espacio y DataCalle #1 fue incorporado. Se ejecuto prepare
del coordinador con el registro completo en HML y luego PRD. Cada entorno
construyo desde main: Espacios f4f61ee61ce2ce7fe9e21475234ecf943c8227a0,
DataCalle 56436c67a319140ccada38c862eba6f65fcf188a y Gestionar
df4bce1a267e486326a2d3dd068268d7b618f8f0. Ambos estados terminaron prepared.

- HML: `/home/sisoc-deploy/.local/state/sisoc-pwa-ready-hml-20260908T202244Z`.
- PRD: `/home/sisoc-deploy/.local/state/sisoc-pwa-ready-prd-20260908T202540Z`.

Cada carpeta conserva herramientas usadas, release/state.json y los runtime.json
con imagenes fijadas por ID. Se probo cada imagen con la configuracion de runtime
del coordinador, en un proyecto Compose temporal sin red ni puertos publicados:
health correcto, UID 101 y filesystem read-only. Los seis contenedores de prueba
se retiraron. Se compararon los contenedores en servicio con el estado anterior
capturado por prepare: no cambiaron. Nginx -t paso en ambos hosts.

Espacio posterior: HML 20 GB libres, 79% de uso; PRD 576 GB libres, 24% de uso.
No se activo la release ni se instalo el snippet nuevo. El permiso temporal sigue
pendiente de retiro al finalizar la intervencion.

La API faltante de HML esta versionada en main mediante SISOC #2452 y #2453,
pero no aparece en config/urls.py de development ni homologacion al verificar.
El endpoint de HML sigue devolviendo 404. Falta esa incorporacion y despliegue
antes de validar autenticacion/sincronizacion.

CI general del PR #2474, ejecucion 34272694992: 4784 tests pasan y fallan tres de
tests/test_admisiones_forms_unit.py. El constructor de InformeTecnicoJuridicoForm
consulta catalogos geograficos sin marca django_db/fixture de base en esos tests.
Este PR no modifica esos archivos; deploy_guard falla como consecuencia del job
pytest. Los 29 tests operativos pasan. No se mezclo una correccion de Admisiones
en la integracion de infraestructura.

## Correccion autorizada de los tres tests bloqueantes

Se reprodujeron los tres fallos en un contenedor local aislado. Los tests prueban
reglas de fecha de mandato y ya simulan BaseModelForm.clean; el constructor ahora
carga catalogos geograficos, una responsabilidad ajena a esas reglas. Se simula
solo `_configurar_selectores_geograficos` en esos tres casos, conservando intactas
las aserciones y la logica de los formularios. Resultado: los 33 tests unitarios
sin marca django_db del archivo pasan; cuatro pruebas con DB quedan para la CI.
No se modifica el acceso a catalogos del producto ni se relaja el bloqueo de DB
de pytest. La nueva ejecucion de CI debe validar la suite completa.

Al actualizar la rama con development (#2473), la comprobacion global detecto
deriva del nombre de indice de ComedorPwaCreateOperation: el modelo lo generaba
automaticamente y la migracion 0059 ya fijaba otro nombre. Se explicita en el
modelo el nombre versionado en 0059, sin alterar el indice de la base ni agregar
una migracion. Esta correccion tambien forma parte de la sincronizacion de main.

Pylint tambien detecto cuatro avisos en api_views_territorial despues de #2473.
Se mueve TerritorialComedorWriteSerializer al modulo api_serializers existente,
manteniendo su import desde la vista y el decorador OpenAPI del ViewSet. Se
separan dos validaciones privadas (jerarquia en edicion y normalizacion de anio)
sin cambiar orden, mensajes ni permisos, y se retiran imports ya sin uso. No se
deshabilitan reglas de lint nuevas. Pylint de ambos modulos: 10/10.
