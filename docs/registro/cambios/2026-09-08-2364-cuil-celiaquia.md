# Celiaquia: validacion de CUIL de 11 digitos y etiqueta CUIL en el front

## Motivo

Dos reportes sobre el mismo dato:

1. El sistema aceptaba un CUIT de 10 digitos y seguia el flujo normal sin avisar.
   Un CUIT valido tiene 11 digitos.
2. En el detalle del expediente el dato se mostraba con la etiqueta "DNI", pero el
   valor exhibido es el CUIL.

## Hallazgo

En Celiaquia `Ciudadano.documento` **siempre es el CUIL**, no un DNI: la validacion
previa solo aceptaba longitudes de 10 u 11 digitos, con lo cual nunca podia contener
un DNI real. El caso de 10 digitos es un CUIL al que le falta un digito.

El CUIT no ingresa por un solo lugar sino por tres, y solo el primero validaba
longitud:

- el Excel masivo de importacion;
- la edicion de un `RegistroErroneo` desde el detalle del expediente;
- el modal "Editar Legajo" (`celiaquia/views/legajo_editar.py`), que no validaba
  ni longitud ni que fueran digitos.

## Cambio

Se agrego `validar_cuil_importacion()` en
`celiaquia/services/importacion_service/impl.py` como regla unica: exactamente 11
digitos numericos, con el mensaje "El CUIL ingresado es invalido: debe tener 11
digitos (se ingresaron N)". La usan los tres puntos de ingreso, tanto para el CUIL
del beneficiario como para el del responsable.

En el front, los tres inputs de CUIL sumaron `pattern="[0-9]{11}"`, `maxlength` e
`inputmode="numeric"`, para que el navegador frene antes de llegar al backend.

La etiqueta "DNI" paso a "CUIL" en `expediente_detail.html`, `cupo_provincia.html`,
`partials/cupo_table.html`, `pago_expediente_detail.html`, `reporter_provincias.html`
y en el mensaje de error de `confirm_envio.py`.

## Que NO se toco (y por que)

No todo "DNI" del front estaba mal. Se dejaron como estaban:

- la comparacion contra RENAPER: `views/validacion_renaper.py` extrae el DNI real
  del CUIL (`documento[2:10]`) y lo muestra, asi que ahi la etiqueta es correcta;
- el PRD del cruce (`pdf_prd_cruce.html`), donde CUIT y DNI son columnas distintas
  del archivo de SINTYS;
- los nombres de documentos fisicos ("Foto DNI", "DNI frente corregido") en
  `legajo_service`;
- `detalle_pago.html`, template muerto: no lo referencia ningun `.py` y usa un
  `persona.dni` que no existe en el modelo.

## Riesgo de datos

Si en produccion ya entraron legajos con un CUIL de 10 digitos (que es lo que
motivo el reporte), esos registros quedan guardados y ahora fallarian al editarse.
Conviene contarlos antes de desplegar.

## Tests

`celiaquia/tests/test_validacion_cuil.py` cubre la funcion de validacion y los tres
puntos de ingreso. Se actualizaron los fixtures de `test_legajo_editar.py` y de tres
casos de `test_registros_erroneos_obligatorios.py`, que usaban documentos de 8
digitos. Suite de celiaquia: 263 tests en verde (253 antes del cambio).
