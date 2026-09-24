# VPSL: ubicación definida en la jornada

## Contexto

Las sedes dejaron de formar parte de la planificación y aprobación previa del
itinerario. La ubicación operativa se conoce al crear cada jornada y se recibe
como un enlace compartido de Google Maps.

## Cambios

- El formulario, detalle, presentación, evaluación y subsanación del itinerario
  ya no usan sedes tentativas ni aprobación de sedes.
- La jornada recibe un nombre de sede, enlace de Google Maps y dirección
  editable. Conserva además latitud y longitud cuando pueden extraerse.
- El alta de jornada exige una localidad perteneciente a la provincia del
  itinerario. La localidad se muestra en el listado de jornadas y en las
  exportaciones.
- El correo electrónico del referente se retira del formulario y de la
  exportación de jornada. El campo histórico se conserva en base de datos.
- El botón `Buscar` resuelve enlaces cortos de `maps.app.goo.gl`, muestra una
  vista previa con pin y completa la dirección cuando el enlace la contiene.
- El detalle de jornada muestra el mapa y un enlace externo a la ubicación
  original.
- El checklist operativo pasa a consultarse y guardarse por jornada, sin
  depender de una `SedeVPSL` preseleccionada. Cuando los tres controles quedan
  en `Sí`, el mismo guardado habilita automáticamente la jornada; la acción
  manual `Habilitar` queda fuera de la interfaz y se conserva solo por
  compatibilidad de rutas existentes.
- El vehículo de la jornada pasa a ser una selección múltiple: se pueden
  agregar o retirar las opciones disponibles desde el mismo desplegable. Los
  valores únicos históricos se migran a la nueva colección.
- Los modelos y relaciones históricos de sedes se conservan por compatibilidad
  de datos, pero quedan fuera del flujo activo de itinerarios y jornadas nuevas.
- Las exportaciones CSV de itinerario y jornada incluyen `Ubicacion sede` con
  las coordenadas en formato `latitud,longitud` cuando están disponibles.

## Seguridad

- Solo se aceptan enlaces HTTPS con hosts exactos de Google Maps.
- La entrada admite `maps.app.goo.gl/<identificador>`, búsquedas canónicas por
  coordenadas y URLs oficiales de Street View con `viewpoint`.
- También se pueden escribir coordenadas como `-34.631040, -58.465853`; se
  validan los rangos, se retiran los espacios y se transforman antes de guardar
  a `www.google.com/maps/search/?api=1&query=latitud,longitud`.
- Otros enlaces de Google, rutas y mapas sin un punto identificable se
  rechazan.
- Se rechazan credenciales en URL, puertos no HTTPS, hosts parecidos y destinos
  de red arbitrarios.
- Cada redirección de un enlace corto se vuelve a validar para evitar SSRF.
- Las URLs canónicas se reconstruyen solo con los parámetros admitidos, para
  que parámetros adicionales no puedan alterar las coordenadas extraídas.
- El endpoint de búsqueda admite hasta 10 intentos por usuario e IP por minuto
  y responde `429` con `Retry-After` cuando se supera el límite.
- La resolución tiene timeout y los errores externos se traducen a mensajes de
  validación sin exponer detalles internos.
- El iframe se construye con coordenadas o dirección normalizadas; nunca usa el
  enlace libre como `src`.

## Limitaciones

Google no siempre incluye calle y altura en el enlace compartido. Cuando solo
hay coordenadas se muestra el pin y la dirección debe completarse manualmente.
No se agregó geocodificación inversa ni una API con clave.

## Validación focalizada

- `python manage.py check`.
- `makemigrations ver_para_ser_libre --check --dry-run`.
- Tests unitarios y de integración de ubicación, permisos, formularios,
  aprobación sin sedes y checklist por jornada.
