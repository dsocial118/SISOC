# Espacios Comunitarios: convivencia de rutas

## Resultado autorizado

Habilitar `/pwa/espacioscomunitarios/` en HML y PRD conservando `/mobile/`
operativa, sin redireccionar usuarios existentes. Los testers del equipo
realizan la aceptacion funcional, de instalacion y offline.

## Implementacion

El mismo commit de `dsocial118/Espacios-Comunitarios:main` produce dos builds
estaticos en una imagen y un contenedor. El build legado mantiene `/mobile/`;
el nuevo usa `/pwa/espacioscomunitarios/` para router, assets y service worker.
El manifiesto nuevo conserva el ID `/mobile/`, y cada build tiene su propio
scope y start_url. No se borran caches, sesiones ni IndexedDB existentes.

Nginx del host conserva el proxy legado y pasa el prefijo nuevo al mismo
puerto 8080 para seleccionar el segundo build. Se instala despues de que la
imagen dual este saludable. DataCalle y Gestionar mantienen sus rutas.

Se conserva `/api` relativo al origen para Espacios. El coordinador fija
explicitamente las URLs HML/PRD para los otros dos frontends.

## Alternativas y limites

Redireccionar la nueva URL a `/mobile/` no satisface el resultado solicitado.
Un router dinamico compartiendo un solo build requeriria adaptar tambien
manifiestos y registro de service workers. Se eligen dos builds para reutilizar
las bases estaticas que la aplicacion ya soporta; aumenta el tiempo de build
y el espacio de la imagen, sin agregar servicios ni dependencias.

La identidad de instalacion no se cambia intencionalmente. El almacenamiento
local es compartido por origen, no aislado por ruta. La instalacion/actualizacion
en navegadores concretos y el uso simultaneo offline quedan a los testers.

## Validacion y rollback

Verificar generacion de Nginx, ambas compilaciones, manifest ID/scope/start_url,
assets, service workers, rutas profundas y destinos API. Probar Nginx antes de
recargarlo. Conservar imagen anterior y copia del include para rollback.
Para revertir: restaurar el include anterior, validar/recargar Nginx y volver
a la imagen anterior. No eliminar almacenamiento de navegadores.
