# #2309 — C3.5: deploy aislado de Dispositivos en QA

## Decisión aprobada

Se agregará un Compose de despliegue distinto del Compose local de Dispositivos.
No crea MySQL, no carga dumps, no monta el checkout y no publica un puerto en
todas las interfaces. Durante la Etapa A consume el schema QA ya existente de
forma temporal, mediante el archivo de entorno privado del checkout aislado.

El proceso web quedará ligado a `127.0.0.1`; no habrá NGINX, gateway ni tráfico
de usuarios en este corte. El routing y los checks de salud públicos pertenecen
a C4. Por lo tanto, C3.5 prueba operación independiente sin introducir un
segundo escritor efectivo.

## Flujo propuesto

Un workflow exclusivamente manual selecciona un destino del contrato C3.3. El
job usa el Environment correspondiente, valida checkout limpio, rama y SHA
confiable, guarda el SHA previo fuera del árbol Git, construye localmente desde
ese SHA y ejecuta primero el rol de migraciones y luego el web. No publica una
imagen ni invoca `deploy_refresh.sh`.

El rollback, también manual, reconstruirá el SHA registrado para el mismo
proyecto Compose. No toca el checkout, contenedores ni datos del monolito.

## Criterios de aceptación

- El contrato de destinos referencia un Compose de despliegue exclusivo.
- El Compose no declara MySQL, volumen de base, dump local ni `.:/sisoc/`.
- El web sólo expone el puerto en loopback y el rol web no ejecuta migraciones.
- El workflow es `workflow_dispatch` exclusivamente; no corre al pushear una
  rama ni llama al deploy monolítico.
- El workflow valida SHA/rama/remoto/checkouts antes de Docker y persiste el
  SHA previo en la ruta declarada para rollback.
- No se ejecutan el workflow, Docker, migraciones ni cambios de QA como parte
  de este corte de código.

## Límites y riesgos

La configuración mantiene credenciales y schema compartidos en Etapa A. No
es una cuenta de mínimo privilegio ni una separación de datos; ambos quedan
para C4/C5. QA sigue sin `compose.dispositivos.deploy.yml` hasta que el PR se
integre en `development`, y esa integración dispara el deploy monolítico
actual: requiere revisión y autorización separadas.
