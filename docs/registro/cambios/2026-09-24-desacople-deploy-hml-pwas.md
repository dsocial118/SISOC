# Deploy HML de SISOC sin coordinación de PWA

El job de homologación falló el 2026-09-24 antes de desplegar el backend:
`deploy_pwas.py prepare` exigía `main` para Espacios Comunitarios, mientras
su checkout HML está correctamente en `homologacion`. El fallo impedía el
deploy SISOC aun cuando la PWA no necesitara actualizarse.

El cambio propuesto hace que el workflow HML extraiga `deploy_refresh.sh` del
SHA del evento y lo ejecute con `--without-mobile`. Conserva la verificación
de revisión remota, rama, checkout limpio, migraciones y healthcheck. Ya no
extrae ni ejecuta
`deploy_pwas.py`, ni prepara o activa imágenes de satélites. Las PWA se
despliegan por sus workflows propios y sus ramas del mismo ambiente.

El cambio es exclusivo de homologación. QA ya ejecutaba el backend sin PWA
por defecto; el job de producción de esta rama permanece sin cambios y su
desacople en `main` sigue sujeto al gate de producción. Antes de fusionar el
PR, validar el test del workflow y revisar el diff. Tras fusionarlo, comprobar
el deploy HML y que los checkouts e imágenes de PWA permanezcan intactos.
Hasta ese run, el despliegue efectivo no está validado. La regresión local
está en `tests/test_deploy_workflow.py`.
