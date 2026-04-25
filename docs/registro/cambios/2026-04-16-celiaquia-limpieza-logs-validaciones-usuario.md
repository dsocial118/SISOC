# Celiaquia: limpieza de logs para validaciones corregibles por el usuario

Fecha: 2026-04-16

## Contexto

En los flujos de importacion, registros invalidos y edicion de legajos de Celiaquia se estaban escribiendo en `error.log` o `warning.log` mensajes asociados a validaciones de datos que:

- ya se notifican al usuario,
- pueden ser corregidas por el mismo desde la interfaz,
- no representan una falla tecnica del sistema.

Segun `docs/ia/ERRORS_LOGGING.md`, estos casos deben resolverse como validacion controlada y no como logging de error o warning.

## Decision

Dejar de loggear validaciones esperables y corregibles por el usuario en estos flujos:

- importacion de legajos,
- reproceso de registros invalidos,
- edicion de registros invalidos,
- edicion manual de legajo.

Se mantienen los logs para errores tecnicos o inesperados.

## Archivos involucrados

- `celiaquia/services/importacion_service/impl.py`
- `celiaquia/views/expediente.py`
- `celiaquia/views/legajo_editar.py`

## Logs que se dejan de escribir

### 1. Warnings por fila/campo en importacion

Antes:

```python
logger.warning("Fila %s: %s (%s)", fila, detalle, campo)
```

Motivo:
- es una validacion del contenido importado,
- el usuario ya recibe ese detalle en el flujo de importacion,
- no agrega señal operativa en logs.

### 2. Error por fila invalida en importacion

Antes:

```python
logger.error("Error fila %s: %s", offset, exc)
```

Motivo:
- la fila rechazada ya queda reflejada en el expediente,
- el usuario puede corregirla desde registros invalidos,
- ensuciaba `error.log` con casos esperables de negocio.

### 3. Error al crear ciudadano durante importacion cuando la causa es `ValidationError`

Antes:

```python
logger.error("Error creando ciudadano en fila %s: %s", offset, exc)
```

Ahora:
- solo se loggea si la excepcion no es `ValidationError`.

Motivo:
- si el problema es un dato invalido, el usuario lo puede subsanar,
- si es una falla tecnica real, el log se conserva.

### 4. Warning de validacion al editar legajo

Antes:

```python
logger.warning("Validación fallida al editar legajo %s: %s", legajo_id, mensaje)
```

Motivo:
- el usuario ya recibe una respuesta `400` con mensaje claro,
- no representa un incidente tecnico.

### 5. Error al reprocesar registro invalido cuando la causa es `ValidationError`

Antes:

```python
logger.error(
    "Error reprocesando registro %s: %s - Datos: %s",
    registro.id,
    e,
    datos_actualizados,
)
```

Ahora:
- solo se loggea si la excepcion no es `ValidationError`.

Motivo:
- si el reproceso falla por validacion, el propio usuario puede corregir el dato,
- el detalle ya queda disponible en el registro erroneo.

## Que se sigue loggeando

Se mantienen los logs en casos como:

- excepciones inesperadas,
- fallas tecnicas,
- errores de infraestructura,
- problemas que el usuario no puede resolver editando datos.

## Validacion

- compilacion de archivos Python modificados,
- tests puntuales del modulo Celiaquia ejecutados en Docker.

## Impacto esperado

- menos ruido en `error.log`,
- mejor separacion entre validacion de negocio y error tecnico,
- mayor señal operativa para soporte y diagnostico.
