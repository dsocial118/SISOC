# VAT: bloquear inscripciones y cerrar comisiones con fecha de fin vencida

## Contexto (bug reportado)

Las comisiones (`ComisionCurso` y `Comision`) no cambian de estado
automaticamente cuando pasa su `fecha_fin`: el estado es 100% manual.
Como la validacion de inscripciones solo miraba `estado` (`curso activo` +
`comision activa`), una comision terminada hace meses seguia aceptando
inscripciones nuevas por API, web publica (Mi Argentina / inscripcion libre)
y backoffice mientras nadie la cerrara a mano.

## Cambio

`VAT/services/inscripcion_service.py`:

- Nuevo helper `InscripcionService._comision_vencida()`: una comision esta
  vencida cuando `fecha_fin < timezone.localdate()`. El dia de `fecha_fin`
  inclusive todavia admite inscripciones; el bloqueo empieza al dia
  siguiente. Si el objeto no tiene `fecha_fin` (mocks o instancias sin
  persistir) el chequeo se saltea.
- `prevalidar_inscripcion()` suma el motivo `MENSAJE_COMISION_VENCIDA`
  ("La comisión ya finalizó y no admite nuevas inscripciones.").
- `crear_inscripcion()` y `crear_inscripcion_oferta()` lanzan `ValueError`
  con el mismo mensaje. Como todos los puntos de entrada (API
  `/api/vat/inscripciones*`, API web publica, views de persona/curso/oferta,
  serializers de inscripcion libre) confunden en estos dos metodos, el
  bloqueo cubre todos los canales, incluida la lista de espera.

### Cierre automatico de estado (segunda parte)

`VAT/services/comision_cierre_service.py` + management command
`cerrar_comisiones_vencidas` (mismo patron que `recargar_vouchers`,
con `--check` / `--execute`):

- Cierra (`estado="cerrada"`) las `ComisionCurso` y `Comision` en estado
  `planificada` o `activa` con `fecha_fin < hoy`. Las `suspendida` no se
  tocan: es una decision manual deliberada.
- Usa el manager default de soft delete, asi que las comisiones borradas
  logicamente no se reprocesan.
- `queryset.update()` no dispara `auto_now`, por eso el servicio setea
  `fecha_modificacion` explicitamente.
- Pensado para cron diario en el servidor (no hay scheduler en el repo,
  igual que `recargar_vouchers`):
  `0 1 * * * cd /sisoc && python manage.py cerrar_comisiones_vencidas --execute`

El bloqueo de inscripciones del service es la red de seguridad para la
ventana entre el vencimiento y la proxima corrida del cron.

Fuera de alcance (decision pendiente): pasar `Curso` a `finalizado` cuando
todas sus comisiones esten cerradas — el curso no tiene fechas propias.

### Mensajes expeditivos y bloqueo por estado (tercera parte)

Los mensajes de "no se puede inscribir" pasan a ser especificos por causa,
centralizados como constantes en `inscripcion_service.py`:

- Por estado del curso: `finalizado` ("El curso ya finalizo: la inscripcion
  esta cerrada."), `cancelado`, `planificado` ("todavia no abrio la
  inscripcion"); idem oferta institucional (`cerrada`/`cancelada`).
- Por estado de la comision: `cerrada` ("La inscripcion a esta comision esta
  cerrada."), `suspendida`, `planificada`.
- Por cupo: "No es posible inscribirse: el cupo esta completo y la comision
  no tiene lista de espera." / "...y la lista de espera tambien.".
- Cupo completo con lista de espera disponible: la prevalidacion agrega el
  campo nuevo `avisos` (no bloqueante) con "El cupo esta completo: la
  inscripcion ingresa en lista de espera." — el front puede mostrarlo antes
  de confirmar. Campo agregado tambien al serializer de respuesta OpenAPI.

Ademas `crear_inscripcion` y `crear_inscripcion_oferta` ahora bloquean por
estado (antes solo la prevalidacion lo miraba, la API directa ignoraba el
estado): comision `cerrada`/`suspendida` y curso `finalizado`/`cancelado`
(oferta `cerrada`/`cancelada`) rechazan el alta con el mismo mensaje.
Decision deliberada: `planificada`/`planificado` NO bloquea el alta directa,
porque el backoffice permite pre-inscribir en comisiones planificadas
(`InscripcionForm` las ofrece); si bloquea la prevalidacion publica.

Las views de backoffice muestran `str(exc)` del service, asi que los textos
nuevos llegan a todos los canales sin cambios adicionales.

## Tests

- Nuevos en `VAT/tests.py`: rechazo por API con comision vencida (400 +
  mensaje), motivo en `prevalidar_inscripcion`, caso borde que permite
  inscribir cuando `fecha_fin` es hoy, y dos tests del command
  `cerrar_comisiones_vencidas` (cierra solo vencidas planificadas/activas
  en ambos modelos, respeta suspendidas y vigentes; `--check` no modifica).
- Fixtures de tests de inscripcion que usaban fechas hardcodeadas ya
  vencidas (`date(2026, 4, 30)`, etc.) pasaron a fechas relativas
  (`timezone.localdate() +/- timedelta`) para que no vuelvan a caducar.

## Validacion

En Docker (entorno canonico): `pytest VAT/tests.py` 199 passed / 3 skipped,
mas `VAT/test_reporte_inscripciones_asistencia.py` y los unit tests
`tests/test_vat_api_web_unit.py`, `tests/test_vat_api_views_unit.py`,
`tests/test_vat_persona_views_unit.py` (18 passed). `black --check` limpio.
