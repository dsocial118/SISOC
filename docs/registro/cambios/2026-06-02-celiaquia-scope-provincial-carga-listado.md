# 2026-06-02 - Celiaquía: aislamiento territorial en carga y listado de expedientes

## Contexto

Seguimiento del issue [#1793](https://github.com/dsocial118/SISOC/issues/1793). El
PR [#1814](https://github.com/dsocial118/SISOC/pull/1814) corrigió la derivación de
la provincia del expediente (ahora se toma del ciudadano, no del perfil legacy del
usuario). Al mostrarse la provincia correcta quedaron expuestos dos huecos de
control de acceso que **no** eran nuevos pero que antes pasaban inadvertidos:

1. **Carga**: un usuario provincial podía importar un Excel con ciudadanos de una
   provincia fuera de su alcance. El filtro de importación dependía de
   `_obtener_provincia_usuario_id`, que solo devuelve una provincia cuando el
   usuario tiene **exactamente una** en su alcance; con multi-provincia (o sin
   alcance resoluble) quedaba en `None` y se importaba **sin filtro provincial**.
2. **Listado / detalle**: `_apply_provincial_expediente_scope` usaba
   `include_own=True`, por lo que un usuario provincial veía y accedía a **todos
   los expedientes que él mismo había cargado**, sin importar la provincia de sus
   ciudadanos (caso reportado: Exped. #367 de Misiones, cargado por un usuario sin
   alcance en Misiones).

Esto era inconsistente con la regla de escritura ya existente en
`celiaquia/permissions.py` (`_expediente_fully_in_territorial_scope`), que exige que
todos los legajos estén dentro del alcance territorial del usuario.

## Cambios aplicados

### Listado y detalle (control de acceso de lectura)

- **`_apply_provincial_expediente_scope`**
  ([celiaquia/views/expediente.py](../../../celiaquia/views/expediente.py)): se quita
  `include_own=True`. Un expediente es visible para un usuario provincial solo si
  tiene **al menos un ciudadano dentro de su alcance territorial**. Se mantiene una
  única excepción: los expedientes **propios aún sin legajos importados** (recién
  creados, sin provincia derivable) siguen siendo accesibles para poder cargar y
  procesar el Excel. Esto afecta de forma centralizada al listado, al detalle y a
  todas las acciones que resuelven el expediente con
  `_get_provincial_expediente_or_404` (procesar, importar, crear legajos, confirmar
  envío).
- **`ReporterProvinciasView`**
  ([celiaquia/views/reporter_provincias.py](../../../celiaquia/views/reporter_provincias.py)):
  mismo criterio; se elimina `include_own` para que el reporte no contabilice
  legajos de otra provincia provenientes de expedientes propios.
- **Vistas de registros erróneos** (`ActualizarRegistroErroneoView`,
  `ReprocesarRegistrosErroneosView`): ahora resuelven el expediente con alcance
  territorial para usuarios provinciales (coordinador/admin sin restricción), en
  lugar de `get_object_or_404(Expediente, pk=pk)` directo.

### Carga (control de acceso de escritura en la importación)

- **`_obtener_provincias_permitidas_ids(usuario)`** (nuevo,
  [importacion_service/impl.py](../../../celiaquia/services/importacion_service/impl.py)):
  devuelve el **conjunto** de `provincia_id` del alcance del usuario (soporta
  multi-provincia). `None` = sin restricción (superusuario / usuario no territorial,
  p. ej. coordinador).
- **`_validar_provincia_permitida_importacion(payload, provincias_permitidas_ids)`**
  (nuevo): si hay restricción y la provincia inferida del ciudadano no pertenece al
  conjunto, lanza `ValidationError`. La fila queda como **registro erróneo**
  (consistente con el comportamiento actual de provincia única) y no se crea el
  ciudadano; el resto del Excel se importa normalmente.
- El gate se aplica al **beneficiario** y al **responsable** en las dos rutas de
  validación: la importación masiva (`_construir_payload_fila_importacion`) y el
  reproceso de registros erróneos (`validar_y_normalizar_payloads_importacion`).

## Decisiones / supuestos

- **Rechazo por fila, no de toda la carga**: las filas de otra provincia se marcan
  como registros erróneos y se importan las válidas. Es lo menos disruptivo y
  consistente con cómo ya se comporta la validación de provincia única. (Si el
  negocio prefiere bloquear toda la importación, es un cambio acotado sobre el mismo
  gate.)
- **Datos existentes**: los expedientes cross-provincia ya cargados (p. ej. #367)
  dejan de verse/accederse para usuarios provinciales. Admin y coordinador los
  siguen viendo y pueden eliminarlos/reasignarlos. No se incluye migración ni script
  de limpieza.
- **Usuarios provinciales = territoriales**: el modelo documentado
  (`Profile.es_usuario_provincial` + `ProfileTerritorialScope`) asume que los
  usuarios provinciales son territoriales. Para un usuario con solo el permiso
  `role_provinciaceliaquia` y sin alcance territorial, el listado/acceso sigue
  restringido a sus propios expedientes (comportamiento previo) y la carga no aplica
  filtro provincial; en la práctica estos usuarios no deberían existir.
- **Granularidad**: la carga valida a nivel **provincia** (lo que pide el issue). El
  listado conserva su granularidad existente (provincia/municipio/localidad) vía
  `build_territorial_scope_q`.

## Validación

- `black --check`: OK sobre los archivos tocados.
- `python -m py_compile`: OK.
- **pytest no se pudo correr localmente**: el Python global del usuario tiene un
  Django incompatible (`ImportError: punycode`) y Docker estaba apagado. Se delega
  a la CI del PR (práctica habitual del repo). Tests nuevos en
  `celiaquia/tests/test_provincia_scope.py` (listado oculta expediente propio de
  otra provincia, detalle 404, validador de provincia en/ fuera de alcance, conjunto
  de provincias permitidas).

## Cómo probar manualmente

1. Usuario provincial con alcance en provincia A (sin Misiones).
2. Subir un Excel con ciudadanos de Misiones → esas filas quedan como registros
   erróneos ("provincia fuera de su alcance"); las de A se importan.
3. El expediente #367 (Misiones) ya no aparece en el listado ni es accesible por
   detalle para ese usuario; sí lo ven admin/coordinador.
4. Un usuario multi-provincia (A + B) puede cargar y ver expedientes de A y de B.
