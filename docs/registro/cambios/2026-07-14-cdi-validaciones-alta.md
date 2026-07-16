# 2026-07-14 - CDI: validaciones del alta (bugs QA TC01-TC26)

## Contexto

Ciclo de QA manual sobre `/centrodeinfancia/crear` (26 casos, TC01-TC26). QA reportó que
el formulario "no comunica los errores". El diagnóstico real es el inverso: **el formulario
aceptaba casi todo**. Salvo `nombre` (y `telefono`, forzado en el form), todos los campos
del modelo son `blank=True, null=True`, y no había validadores de formato. No aparecían
mensajes porque no se generaba ningún error.

Consecuencia más grave (BUG-01, crítico): un CDI se podía guardar con `provincia = NULL`.
Como `CentroDeInfanciaDetailView` y el listado filtran por scope territorial
(`aplicar_scope_centros_cdi`), ese registro no matchea ningún filtro provincial: el
redirect post-guardado daba **404** y el CDI quedaba invisible para siempre. En la base
había 4 registros así (sobre 29 totales).

## Cambios aplicados

- `core/validators.py`: validadores reutilizables nuevos — `validate_cuit` (con dígito
  verificador y rechazo de CUIT en cero), `validate_solo_letras`, `validate_telefono_ar`
  (6-11 dígitos), `validate_codigo_postal_ar` (4 dígitos, 1000-9999), `solo_digitos`.
- `centrodeinfancia/forms.py` (`CentroDeInfanciaForm`):
  - `CAMPOS_OBLIGATORIOS`: 22 campos, según la columna `Req.Funcional` de la planilla de QA.
  - `_aplicar_requeridos()`: obligatorios en **alta y en edición** (decisión de PM).
  - `_aplicar_campo_ambito()`: `ambito` pasa a obligatorio; se quita "Sin información" de
    las opciones elegibles y del default, y se fuerza un placeholder vacío.
  - Validación de nombre/organización/referente (solo letras), CUIT, teléfonos, código
    postal, año de inicio (AAAA, entre 1900 y el año actual) y coordenadas.
  - `_aplicar_anio_inicio()`: en edición el widget numérico recibía `"1995-01-01"` y se
    mostraba vacío; ahora precarga el año.
- `centrodeinfancia_form.html`: "Modalidad" y su campo condicional "Modalidad — otra" se
  mueven de la sección Funcionamiento a Información Básica (pedido de UX de QA, confirmado
  por PM). Es solo layout: no cambia el modelo, el form ni la base.
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html`: se elimina el
  validador JS propio que hacía `preventDefault()` y solo pintaba el borde en rojo **sin
  escribir ningún mensaje** — al bloquear el submit, impedía que se renderizaran los
  mensajes de crispy. Ahora valida el servidor y el JS solo hace scroll/foco al primer error.

## Impacto esperado

- No se pueden crear más CDIs incompletos. BUG-01 (404 + registro huérfano) y BUG-02
  (guardar con errores) dejan de reproducirse.
- Los mensajes de error inline aparecen sin trabajo de UI adicional: crispy ya los
  renderizaba, el JS los estaba tapando.
- Los CDIs históricos incompletos siguen siendo editables.

## Decisiones de producto (PM, 2026-07-14)

- **Latitud/longitud**: **optativas**. Pasarían a obligatorias solo si se implementa la toma
  automática de ubicación por GPS, que no está en esta instancia (queda como ticket aparte).
  Se validan con el rango de Argentina (lat -55/-21, lon -74/-53) en vez de -90/90 y
  -180/180, porque QA pide rechazar `34.60879` como fuera de rango.
- **Obligatorios en alta y edición**: sí, sin excepciones. Los datos hoy cargados son de
  prueba y se van a borrar, así que no hace falta contemplar CDIs históricos incompletos.
- **`ambito`**: obligatorio, sin default "Sin información".
- **CUIT contra ARCA/ANSES**: deseable a futuro, **fuera del alcance de este ticket**. Por
  ahora se valida formato + dígito verificador. Ver "Riesgos".

## Pendiente

- **BUG-09 (Servicios/Multiedad)**: no se pudo reproducir; el test de persistencia pasa.
  El PM está contactando a QA para que especifique los pasos.

## Validación

- `pytest centrodeinfancia/ tests/` → 2277 passed, 2 skipped.
- `centrodeinfancia/tests/test_centrodeinfancia_form.py` reescrito: 81 tests, cubre cada
  bug de la planilla y los casos que QA aprobó, como no-regresión.
- `black`, `pylint`, `djlint` OK.

## Riesgos y rollback

- **Riesgo principal (asumido por PM):** los 29 CDIs que hoy existen quedan **ineditables**
  hasta que se completen todos sus campos obligatorios (17 sin modalidad, 15 sin
  departamento/CP/CUIT, 14 sin mail...). Es aceptable porque son datos de prueba y se van a
  borrar antes de la puesta en producción. **Si por algún motivo esos datos no se borran, hay
  que revisar esta decisión**: el mismo form sirve al alta y a la edición.
- **Atención QA:** el CUIT `30-12345678-9` que la planilla usa como caso válido (TC03/TS05)
  **no es un CUIT real** — su dígito verificador es `1`. Ahora se rechaza, correctamente.
  Para retestear usar `20-44535030-4`.
- **CUIT no se verifica contra ARCA/ANSES:** se valida que el número sea *formalmente*
  correcto, no que exista y esté operativo. Un CUIT bien formado pero inexistente se acepta.
- **Rollback:** revertir el commit. No hay migraciones ni cambios de datos.
