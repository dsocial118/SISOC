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
