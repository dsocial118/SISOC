# Web rendicion: revision por documento y subsanacion

## Contexto

En el detalle web de rendiciones mensuales ya se visualizaba la documentacion
cargada desde SISOC Mobile, pero faltaba continuar el flujo de revision por
documento.

## Cambio realizado

- Se agrego la operacion de negocio para revisar un documento presentado y
  cambiarlo a:
  - `validado`
  - `subsanar`, exigiendo observaciones
- La revision se realiza por documento desde el detalle web de la rendicion.
- Cada documento mantiene su propio estado y sus observaciones.
- Cuando un documento queda en `A subsanar`, la observacion persistida se
  muestra debajo de su fila con el formato `Observaciones: ...`, alineada a
  la izquierda.
- La observacion editable y la observacion persistida se muestran en una fila
  completa inmediatamente debajo del documento, sin separacion visual entre
  ambas filas, para reforzar la asociacion con el archivo correspondiente.
- Cada cambio de estado de documento revisado desde web genera ademas una
  notificacion mobile en la bandeja del espacio usando el canal existente de
  `comunicados`, para que el usuario relacionado vea si debe subsanar o si un
  documento fue validado.
- La notificacion mobile se replica a los espacios del mismo proyecto/alcance
  de la rendicion, para que tambien aparezca si el usuario entra por otro
  espacio relacionado dentro del mismo contexto operativo.
- En el detalle mobile de rendicion, cada archivo queda expuesto con su estado
  visible (`Presentado`, `Validado`, `A subsanar`) y con sus observaciones
  cuando corresponda.
- El detalle del mensaje mobile de una revision de rendicion ahora expone una
  accion directa para abrir la rendicion asociada desde la propia notificacion.
- El detalle web de la rendicion ahora muestra tambien el `Usuario creador`
  junto a los datos generales, y las nuevas rendiciones guardan ese dato tanto
  si se crean desde Web como desde Mobile.
- La rendicion ahora persiste tambien `usuario_ultima_modificacion`, y ese dato
  se actualiza en las operaciones principales de Web y Mobile que cambian su
  contenido o su estado.
- En Mobile, el detalle offline-first de rendicion ahora refresca desde backend
  cuando no hay cambios locales pendientes, para reflejar correctamente estados
  revisados como `Validado` o `A subsanar`.
- Las notificaciones mobile originadas por revision de rendicion se listan solo
  para usuarios PWA que tienen acceso al espacio y el permiso especifico de
  rendicion mobile.
- La documentacion mobile vuelve a quedar bloqueada fuera de `elaboracion`:
  por ahora, una vez enviada a revision no se permite agregar ni borrar
  archivos hasta definir el flujo completo de subsanacion.
- Se habilito la subsanacion mobile por tipo de documento: en
  `Comprobante/s` y `Documentacion Extra` se pueden cargar nuevos archivos
  manteniendo historial del observado; en las categorias de archivo unico, la
  nueva carga reemplaza al observado. En `subsanar` se permite reenviar la
  rendicion, pero no borrarla manualmente.
- En las notificaciones mobile de rendicion se dejo de rotular el contexto con
  el nombre del espacio/comedor desde el que se accede, porque la rendicion se
  comunica como objeto de proyecto y no como mensaje de un unico comedor.
- El comunicado de rendicion ahora identifica el evento por `proyecto` y
  `convenio` en el titulo y en el cuerpo, para evitar asociarlo visualmente a
  un solo comedor cuando el alcance real es el proyecto.
- La campanita de la PWA ahora agrupa notificaciones de rendicion del mismo
  `rendicion_id`, para evitar listas repetidas cuando se revisan varios
  documentos de una misma rendicion.
- Se agrego soporte real de web push para la PWA: la app ahora puede pedir
  permiso del navegador, registrar una suscripcion por usuario/dispositivo,
  recibir una notificacion nativa del sistema cuando se revisa una rendicion
  y abrir directamente el detalle correspondiente al tocarla.
- Se documento el checklist operativo de despliegue en
  `docs/operacion/pwa_web_push_deploy.md` para QA y Produccion.
- Se corrigio la cola offline de la PWA para que, en subsanacion de categorias
  de archivo unico, no intente borrar antes el documento observado, porque ese
  borrado manual esta bloqueado por backend y dejaba uploads pendientes de
  sincronizacion sin avanzar.
- En Mobile, `Comprobantes` y `Documentacion Extra` mantienen visible la
  carga de archivos mientras la rendicion siga editable; en `subsanar` el
  bloque para adjuntar nuevas subsanaciones no se oculta despues del primer
  upload y recien deja de estar disponible cuando se presiona `Enviar cambios`.
- En el detalle de rendicion, tanto en Web como en Mobile, las cargas hechas
  como subsanacion ahora se muestran debajo del documento observado como un
  historial ordenado por fecha descendente, conservando los datos visibles del
  archivo y mostrando el estado visual `Subsanado`.
- La PWA ahora separa `outbox`, rendiciones, archivos y colaboradores offline
  por usuario autenticado (`user_key`), de modo que cambiar de cuenta en el
  mismo navegador no mezcle pendientes ni sincronice acciones con el token de
  otro usuario. Para no perder datos locales viejos, la primera sesion que se
  revalida despues de este cambio reclama los registros legacy que todavia no
  tenian usuario asociado.
- Las notificaciones de rendicion en la campanita dejan de acumularse como
  historial abierto: antes de publicar una nueva se archivan las anteriores de
  esa misma rendicion, y cuando la rendicion se reenvia a revision o queda
  finalizada tambien se archivan para que desaparezcan de la bandeja activa.
- Ademas, el motor de sincronizacion limpia automaticamente los deletes viejos
  ya encolados para archivos observados en `subsanar`, de modo que una cola
  trabada por versiones anteriores pueda destrabarse al volver a sincronizar.
- La pantalla de mensajes de organizacion en la PWA ahora consulta mensajes por
  lotes y tolera fallos parciales por espacio, evitando timeouts de 15 segundos
  cuando un usuario tiene muchos espacios o el backend responde mas lento.
- Desde la bandeja `/app-org/mensajes`, las tarjetas de notificaciones de
  rendicion ahora abren directo el detalle de la rendicion asociada, sin pasar
  por un mensaje intermedio.
- La bandeja `/app-org/mensajes` de la PWA ahora separa los items en
  `Notificaciones generales`, `Comunicaciones a espacios` y
  `Notificaciones de Rendiciones`, ocultando por completo las secciones vacias.
  Ademas, se corrigieron los textos con acentos visibles en esa vista para que
  no dependan del encoding del bundle.
- En la bandeja de organizacion, las alertas de rendicion dejaron de
  presentarse como un tipo mas de mensaje: ahora se muestran en un bloque
  separado de `Notificaciones`, mientras que los comunicados quedan dentro del
  bloque `Mensajes`.
- La separacion entre `Mensajes` y `Notificaciones` en la PWA ahora tambien es
  de navegacion: el menu inferior sigue abriendo `/app-org/mensajes` para
  comunicados, mientras que la campanita del header abre `/app-org/notificaciones`
  solo con alertas de rendicion.
- El contador general de notificaciones de la organizacion ahora respeta el
  mismo agrupado por `rendicion_id` que la bandeja: varias alertas no leidas de
  documentos distintos de una misma rendicion cuentan como una sola
  notificacion en la campanita principal.
- El endpoint de mensajes PWA expone ahora contadores agrupados de rendicion
  (`unread_grouped_count`, `unread_rendicion_ids` y
  `unread_espacio_non_rendicion_count`) para que la campanita principal no se
  desfasen cuando conviven comunicaciones de espacios con varias alertas de una
  misma rendicion.
- El motor de sincronizacion mobile ahora reinterpreta como exito un
  `UPLOAD_RENDICION_FILE` de subsanacion que el backend rechaza por duplicado
  si el archivo ya aparece efectivamente en el detalle remoto; con eso se
  limpia la cola local y se destraba el `PRESENT_RENDICION` posterior.
- La rehidratacion offline del detalle de rendicion ahora vuelve a enlazar
  correctamente subsanaciones ya cargadas en backend aunque el nombre local del
  archivo no coincida de forma exacta, priorizando tambien el
  `documento_subsanado`. Esto evita que queden uploads pendientes fantasma y la
  nubecita amarilla al reenviar una rendicion subsanada.
- El centro de sincronizacion mobile ahora muestra etiquetas legibles para las
  acciones de outbox de rendicion y sus archivos, en lugar de codigos tecnicos
  como `PRESENT_RENDICION` o `UPLOAD_RENDICION_FILE`.
- La pantalla de sincronizacion mobile ahora explicita el ciclo de reintentos:
  muestra el error recibido, indica cuando una accion se esta intentando en ese
  momento y, si queda programada para retry automatico, muestra la cuenta
  regresiva hasta el proximo intento.
- El detalle mobile de una rendicion ahora bloquea nuevas cargas, borrados y
  reenvios mientras la propia rendicion tenga un envio pendiente de
  sincronizacion (`pending_action=present` con `sync_status=pending`), para
  evitar superponer cambios sobre un envio en curso.
- Cuando el backend rechaza un `PRESENT_RENDICION` por una validacion de
  negocio (por ejemplo, porque todavia hay documentacion pendiente de
  subsanar), la PWA ya no entra en loop de retry automatico: deja el envio en
  error terminal, limpia el `pending_action=present` y vuelve a habilitar la
  edicion para que el usuario complete la subsanacion faltante.
- Como salida provisoria operativa, el centro de sincronizacion agrega la
  accion manual `Descartar este pendiente` para items `PRESENT_RENDICION`. Al
  usarla, elimina ese outbox puntual y destraba la rendicion local para poder
  seguir cargando o reenviando cambios.
- El detalle de documentacion para categorias con historial de subsanacion
  (`Comprobantes` y `DocumentaciÃ³n Extra`) ahora promueve como archivo
  principal el ultimo documento de la cadena que vuelve a quedar observado,
  dejando los anteriores como historial. Con esto, web y mobile muestran como
  vigente el archivo que realmente sigue pendiente de subsanar.
- El estado global de la rendicion se recalcula automaticamente:
  - si existe al menos un documento `subsanar`, la rendicion pasa a
    `Presentacion a subsanar`
  - si todos los documentos activos quedan `validado`, la rendicion pasa a
    `Presentacion finalizada`
  - en cualquier otro caso queda en `Presentacion en revision`

## Alcance de esta fase

- Se cubre la revision web por documento sobre archivos ya presentados.
- La API mobile ya exponia `estado` y `observaciones` por documento en el
  detalle, por lo que no fue necesario ampliar ese payload en esta fase.
- La web push se activa solo si el entorno define claves VAPID y si el backend
  tiene disponible la libreria de envio correspondiente.

## Supuestos

- La revision web de documentos aplica sobre documentos en estado
  `Presentado`.
- La subsanacion y sus observaciones deben persistir por documento, no en un
  comentario global unico de la rendicion.

## Validacion

- `docker compose exec django pytest tests/test_rendicioncuentasmensual_services_unit.py tests/test_rendicioncuentasmensual_views_unit.py -q`

- El detalle mobile de rendiciones ahora distingue visualmente una rendición bloqueada por estado de una rendición que se está enviando: durante la sincronización conserva el botón con spinner y el texto 'Sincronizando envío...' en lugar del mensaje fijo de que ya no admite cambios.

- Al confirmar el modal de envío exitoso de una rendición desde mobile, la PWA vuelve automáticamente al listado de rendiciones del espacio en lugar de quedarse en el detalle.
