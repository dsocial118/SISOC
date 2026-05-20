# 2026-05-20 — Dispositivos: desdoble de Domicilio y Teléfono

## Contexto
Evolutivo del formulario "Situación de Calle / Dispositivos" (issue #1655). Tickets 7, 9 y 10 piden separar:
- `domicilio_institucion` en `calle` + `altura`.
- `telefono_contacto` en `telefono_prefijo` + `telefono_numero`.

## Decisión
- Reemplazo directo de los campos viejos por los nuevos, sin back-fill ni período de deprecación.
- Confirmado con PM que **no hay datos cargados** en el ambiente productivo de la app, por lo que la estrategia conservadora (mantener legacy + back-fill) que originalmente se planteó no es necesaria.

## Cambios

### Modelo (`dispositivos/models.py`)
- Removidos: `domicilio_institucion`, `telefono_contacto`.
- Agregados: `calle` (CharField 255), `altura` (CharField 50), `telefono_prefijo` (CharField 10), `telefono_numero` (CharField 20). Todos con `blank=True` (convención Django: required se enfuerza en el form).

### Migración
- `dispositivos/migrations/0005_remove_dispositivo_domicilio_institucion_and_more.py`: RemoveField (2) + AddField (4) en una sola operación.

### Form (`dispositivos/forms.py`)
- `Meta.fields`: removidos los viejos, agregados los 4 nuevos.
- En `__init__`:
  - Labels en español: "Calle", "Altura", "Prefijo", "Teléfono".
  - `required=True` explícito para los 4 nuevos (operador debe completarlos).
  - Widget attrs `inputmode="numeric"`, `pattern=r"\d+"` y `maxlength` en prefijo y número.
  - Help text en `telefono_numero`: "Tanto el prefijo como el teléfono deben ingresarse sin puntos ni guiones".
- Nuevos `clean_telefono_prefijo` y `clean_telefono_numero` que strip-ean no-dígitos y validan no-vacío.

### Template (`dispositivos/templates/dispositivos_form.html`)
- La fila de identificación pasa de `[Domicilio (4)] [Teléfono (2)] [Correo (2)]` a `[Calle (3)] [Altura (1)] [Prefijo (1)] [Teléfono (2)] [Correo (3)]`, todos lado a lado en la misma fila.

### Vista (`dispositivos/views.py`)
- Detalle: reemplaza filas "Domicilio" y "Teléfono de contacto" por "Calle", "Altura" y un combinado "Teléfono" = `{prefijo} {numero}`.

### JS (`static/custom/js/dispositivoFormModerno.js`)
- Nuevo `initializeNumericInputs()` que filtra caracteres no numéricos en `id_telefono_prefijo` e `id_telefono_numero` mientras se tipea. Necesario porque el form lleva `novalidate` y el atributo `pattern` no muestra mensajes nativos.

### Tests (`dispositivos/tests/*`)
- Reemplazo de los datos POST y de `_crear_dispositivo` para usar los nuevos campos.

## Riesgos / pendientes
- Esta PR asume cero datos en producción. Si llegara a haber alguno en otro ambiente, la migración los va a perder porque hace `RemoveField` directo (no `RunPython` de back-fill).
- Si se mergea **antes** que `dispositivos-micro-ajustes` (#????), va a haber conflicto en `forms.py` (los dos toques en `__init__`) y en `dispositivoFormModerno.js` (los dos definen `NUMERIC_ONLY_INPUT_IDS`). La resolución es combinar las dos listas y poner ambos bloques de widget attrs.

## Cómo probar
1. `docker exec sisoc_2-django-1 python manage.py migrate dispositivos`.
2. Crear un dispositivo nuevo: la sección 1 muestra Calle, Altura, Prefijo y Teléfono como campos separados. Intentar tipear letra en prefijo/teléfono no permite. Submit sin completarlos rechaza.
3. Editar un dispositivo y abrir el detalle: las labels "Calle", "Altura" y "Teléfono" (prefijo + número combinados) se renderizan correctamente.
