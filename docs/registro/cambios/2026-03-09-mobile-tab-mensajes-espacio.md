## Cambio

Se conecto la tab de mensajes del hub del espacio en Mobile con la API PWA de mensajes.

## Alcance

- Se reemplazo el placeholder de mensajes del espacio por una pantalla funcional.
- Se reemplazo el placeholder de `Mensajes` del menu inferior de organizacion por una bandeja consolidada.
- Se agrego cliente API para listar mensajes y marcarlos como vistos.
- Al abrir un mensaje no leido, Mobile dispara el marcado como visto.
- Se agregaron badges de no leidos en el boton `Mensajes` del hub y en la campana del header.
- La campana del header ahora agrega mensajes sin leer de todos los espacios cuando la organizacion esta en el listado general.

## Implementacion

- Nueva pantalla `SpaceMessagesPage` en `mobile/src/features/home/`.
- Nueva pantalla `OrganizationMessagesPage` para consolidado multi-espacio.
- Nuevo cliente `mobile/src/api/messagesApi.ts`.
- La ruta `app-org/espacios/:spaceId/mensajes` ahora consume la API real de PWA.
- Se sumo un hook liviano para reutilizar el conteo de mensajes no leidos por espacio y sincronizar badges.
- Se extendio ese hook para sumar no leidos por todos los espacios accesibles y resolver mejor el destino de la campana.
- Se corrigio el contador global de la campana para que use el total autoritativo por espacio y no solo los mensajes visibles en la bandeja consolidada.
- Se ajusto la posicion visual del badge de la campana para subirlo y agregarle borde blanco.
- Se alineo el header de la bandeja de mensajes de organizacion con el patron del selector de espacios: `Organizacion` arriba y `Mensajes` abajo.
- Se reposiciono el badge de la campana a la esquina superior derecha del icono y se mejoro la legibilidad del numero.
- Se agrego un cache en memoria de no leidos por espacio para que el badge de `Mensajes` en el hub pueda aparecer mas rapido y luego reconciliar con la API.
- Se agrego persistencia en `sessionStorage` para espacios y conteos de no leidos, para acelerar la carga inicial de la campana tambien despues de recargas.
- Se extendio esa lectura persistida al badge del hub del espacio para que no dependa solo del cache en memoria.
- La lectura de mensajes paso a una pagina dedicada por mensaje para soportar mejor texto largo y adjuntos.
- En el detalle de mensaje se elimino el boton inferior de volver para usar solo la navegacion del header.

## Impacto

- La organizacion puede ver en Mobile los comunicados enviados al espacio desde la webapp.
- El estado de lectura se sincroniza con el backend PWA al abrir cada mensaje.
- El hub del espacio y la campana del header muestran cuántos mensajes siguen sin leer.
- En la vista de listado de espacios, la campana refleja el total agregado de mensajes sin leer entre todos los espacios.
- El boton `Mensajes` del menu inferior permite ver una bandeja unificada de mensajes de todos los espacios.
- La campana mantiene el conteo correcto aunque la bandeja consolidada no tenga cargados todos los mensajes visibles de un espacio en una sola pagina.
- La campana puede mostrar un valor inmediato reutilizando cache persistente y luego refrescar contra la API.
- El badge de `Mensajes` dentro del hub del espacio puede renderizar un valor inmediato si ya hubo navegacion previa por pantallas que conocen esos conteos.
- El badge de `Mensajes` dentro del hub del espacio tambien puede recuperar el ultimo conteo persistido del usuario despues de una recarga.
- Los mensajes de espacio y de la bandeja consolidada ahora abren un detalle propio, donde se marca la lectura y se muestran imagenes o documentos adjuntos.
