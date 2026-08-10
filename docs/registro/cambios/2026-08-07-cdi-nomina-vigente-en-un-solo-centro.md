# 2026-08-07 - CDI: una única nómina vigente por persona

## Contexto

El alta de destinatario en un CDI (`/centrodeinfancia/<pk>/nomina/crear/`) impedía
duplicar a una persona **dentro del mismo centro**, pero permitía que quedara registrada
simultáneamente en varios Centros de Infancia. Se pide una única inscripción vigente por
persona en todo el programa, sin revelar en qué centro está registrada.

Regla funcional: **vigente = estado Activo o Pendiente**. Los registros en Baja no
bloquean, lo que preserva el flujo de derivación (el origen pasa a Baja y el destino se
crea Pendiente en la misma transacción).

## Cambios aplicados

### `centrodeinfancia/services.py`

- `ESTADOS_NOMINA_CDI_VIGENTE` y `MENSAJE_NOMINA_VIGENTE_EN_OTRO_CENTRO` (mensaje neutro,
  fuente única para todos los flujos).
- `tiene_nomina_cdi_vigente_en_otro_centro(ciudadano_id, centro_id, excluir_nomina_id)`:
  devuelve **sólo un booleano**, a propósito — quien llama no puede informar ni inferir de
  qué centro se trata. El manager por defecto de `NominaCentroInfancia` ya excluye los
  registros dados de baja lógicamente, así que los dos sentidos de "baja" (estado y soft
  delete) quedan fuera del cálculo de vigencia sin filtros extra.
- `bloquear_ciudadano_para_nomina_cdi(ciudadano_id)`: toma el lock de fila del ciudadano
  dentro de la transacción en curso.
- `puede_reactivar_nomina_cdi_bajo_bloqueo(...)`: revalida y serializa la transición
  desde Baja inmediatamente antes de persistirla.
- Derivación (`transferir_ciudadano_entre_centros`): la validación de destino se extrajo a
  `_validar_vigencia_para_derivacion` (se usaba duplicada dentro y fuera de la
  transacción) y ahora también cubre la vigencia en un **tercer** centro, que antes
  pasaba. El mensaje del caso "ya está en el destino" se mantiene (nombra al centro que el
  usuario eligió); el del tercer centro es el neutro.

### `centrodeinfancia/views.py`

- `_crear_nomina_con_bloqueo` devuelve `(creado, motivo)` en lugar de un booleano, con
  `MOTIVO_NOMINA_DUPLICADA_MISMO_CENTRO` / `MOTIVO_NOMINA_VIGENTE_OTRO_CENTRO`, para que
  la vista elija el mensaje sin recibir datos del otro centro.
- Rechazo por vigencia en otro CDI: se re-renderiza el formulario con el error no asociado
  a campo, en vez de redirigir. Con 16 secciones cargadas, perder el formulario es caro; el
  duplicado en el mismo centro sigue redirigiendo a la nómina (donde la persona ya está).

### `centrodeinfancia/forms.py`

- `NominaCentroInfanciaBaseForm._validar_vigencia_unica_cdi`: cierra el bypass por
  edición (pasar una ficha de Baja a Activo/Pendiente). Cubre los dos flujos de edición
  (página completa y ajax) porque ambos heredan del form base.
- **Sólo valida la transición hacia un estado vigente.** Una ficha que ya estaba vigente
  puede seguir editándose: los duplicados históricos están fuera de alcance y no deben
  volverse ineditables.
- `NominaCentroInfanciaAdminForm`: aplica la misma validación al alta y a la reactivación
  desde Django admin, sin revelar el otro centro.

### Restauración lógica

- `validar_restauracion_nomina_cdi` se ejecuta dentro de la transacción de restauración
  genérica mediante el hook declarativo `SOFT_RESTORE_VALIDATOR`. Si una ficha
  Activa/Pendiente borrada lógicamente entraría en conflicto con otro CDI, la restauración
  se rechaza con el mensaje neutro y permanece en papelera.

## Concurrencia

El bloqueo previo era `select_for_update` sobre el **centro**, que no sirve para esta
regla: los intentos simultáneos ocurren justamente en centros distintos. Ahora se toma
primero el lock de fila del **ciudadano** (orden de adquisición único, para no introducir
deadlocks), tanto en el alta como en la derivación.

**El lock de fila solo no alcanzaba.** InnoDB corre en REPEATABLE READ y el proyecto no
usa `ATOMIC_REQUESTS`, así que la transacción arranca en el `atomic()` del alta — pero en
el camino "ciudadano nuevo" hay lecturas comunes *antes* de tomar el lock (búsqueda de
sexo, de ciudadano por DNI). Esas lecturas fijan el snapshot de la transacción, y una
verificación posterior sin lock lo usaría: un alta concurrente commiteada entre el
snapshot y la adquisición del lock quedaría invisible (write skew), y se crearían dos
registros vigentes.

Por eso las verificaciones de los caminos que escriben usan lectura con lock
(`tiene_nomina_cdi_vigente_en_otro_centro(..., bloquear=True)`, y lo mismo en la
revalidación de la derivación y en el chequeo de duplicado del mismo centro): una lectura
con lock siempre ve la última versión commiteada y, al no haber filas, toma el gap lock
del índice de `ciudadano_id`, que además frena el insert simultáneo. La validación de
edición mantiene el error temprano del formulario y se **revalida bajo el mismo lock**
justo antes del `save`, tanto en la página completa como en el modal AJAX.

**No se agregó constraint de DB a propósito:**

- Una `UniqueConstraint(condition=...)` parcial no funciona en MySQL 8.4 — Django la
  ignora en backends sin partial indexes, así que daría una falsa sensación de garantía.
- Los duplicados históricos están fuera de alcance; una constraint dura rompería el deploy
  si existen.

Emularla con columna generada + índice único es posible pero desproporcionado para el
alcance del ticket. La garantía es de aplicación, apoyada en el row lock de InnoDB.

## Validación

- `centrodeinfancia/tests/test_nomina_vigencia_unica.py` (nuevo): alta permitida
  sin vigencia; bloqueo por Activo y por Pendiente (parametrizado); reingreso tras Baja y
  tras baja lógica; duplicado en el mismo centro conservado; mensaje neutro en la vista sin
  filtrar nombre ni enlace del centro de origen; altas concurrentes en MySQL; edición
  (form y ajax), admin y restauración; derivación con tercer centro y camino feliz de
  derivación intacto.
- `test_nomina_integridad.py`: actualizado al nuevo retorno `(creado, motivo)`.
- `pytest centrodeinfancia` → **515 passed**. `pytest tests -k "cdi or centrodeinfancia or
  nomina or ciudadano"` → **223 passed**. `black` y `pylint` (10.00/10) OK.

### Límite conocido de los tests de concurrencia

En SQLite `select_for_update` es un no-op, así que la suite por defecto no puede provocar
una carrera real. La prueba marcada `mysql_compat` usa dos transacciones simultáneas sobre
MySQL para verificar que sólo una alta del mismo destinatario queda vigente. El bloqueo
efectivo lo aporta InnoDB.

## Fuera de alcance / gaps conocidos

- No se corrigen duplicados históricos ni se agrega migración de datos.
- `NominaCentroInfanciaFormEdit` no se tocó: no está conectado a ninguna URL.

## Riesgos y rollback

- Si en producción hay personas con vigencia en más de un CDI, la nueva regla no las
  modifica (sólo bloquea altas nuevas), pero **su derivación va a empezar a fallar** con el
  mensaje neutro. Conviene contar esos casos antes de desplegar:

  ```sql
  SELECT ciudadano_id, COUNT(DISTINCT centro_id) AS centros
  FROM centrodeinfancia_nominacentroinfancia
  WHERE deleted_at IS NULL AND estado IN ('activo', 'pendiente')
  GROUP BY ciudadano_id HAVING centros > 1;
  ```

- **Rollback:** revertir el commit. No hay migraciones ni cambios de schema involucrados.
