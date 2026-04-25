# Celiaquia: subsanacion de registros erroneos con nacionalidad obligatoria y marcado visual por campo

Fecha: 2026-04-15

## Contexto

En el detalle de expedientes de Celiaquia, los `registros_erroneos` permitian
editar filas fallidas de importacion, pero habia dos problemas funcionales:

- `nacionalidad` podia aparecer preseleccionada en `Argentina` aunque el valor
  importado fuera invalido o faltante.
- el usuario no veia con claridad que campo puntual estaba invalidando la
  subsanacion.

Esto generaba una mala UX y podia inducir correcciones engañosas: el registro
seguia bloqueado, pero el formulario no mostraba con precision que dato faltaba
o era incorrecto.

## Cambio realizado

Se ajusto el flujo de `registros_erroneos` en `expediente_detail` para que:

1. `nacionalidad` no se autocomplemente cuando el dato original es invalido o
   vacio.
2. el selector quede en `Seleccionar...` hasta que el usuario elija un valor
   valido.
3. la vista derive `invalid_fields` desde `mensaje_error` y los exponga al
   template.
4. los campos invalidos en `Editar Datos - Fila X` se rendericen con un
   recuadro rojo sutil, manteniendo el estilo base del modulo.
5. la resolucion visual de nacionalidad reutilice la misma logica del importador,
   incluyendo el fallback `pais_a_nacionalidad` cuando el dato es resoluble.

## Decision de UX

Se eligio:

- no asumir una nacionalidad por defecto en registros invalidos,
- no agregar fondo rojo persistente,
- no cambiar la paleta base del modulo,
- marcar solo con recuadro/outline rojo suave los campos invalidos.

Motivo:

- preservar consistencia visual con la branch,
- destacar el error sin introducir ruido,
- evitar que una sugerencia visual se confunda con un dato ya corregido.

## Archivos tocados

- `celiaquia/views/expediente.py`
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `static/custom/js/registros_erroneos.js`
- `static/custom/css/registros_erroneos.css`
- `celiaquia/tests/test_registros_erroneos_obligatorios.py`

## Testing agregado o ajustado

Se reforzaron regresiones para cubrir:

- nacionalidad editable sin autoseleccion por defecto,
- resolucion visual por `pais_a_nacionalidad`,
- exposicion de `invalid_fields` para nacionalidad invalida,
- exposicion de `invalid_fields` para `altura` faltante,
- respuesta backend con `invalid_fields` en validaciones parciales.

## Validacion ejecutada

Se ejecuto la validacion puntual del flujo en Docker:

```bash
docker compose exec django pytest celiaquia/tests/test_registros_erroneos_obligatorios.py -q
```

Resultado:

```text
21 passed in 24.68s
```

## Riesgos y follow-up

- `invalid_fields` hoy se deriva desde mensajes de error conocidos. Si cambian
  los textos de validacion, conviene mantener sincronizado el mapeo de campos.
- si en el futuro cambian los selectores o estructura del formulario de
  `registros_erroneos`, conviene revisar los tests HTML para mantenerlos
  acotados al bloque correcto del form.
