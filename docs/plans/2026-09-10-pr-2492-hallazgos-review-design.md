# PR 2492: correcciones de integridad para menores y responsables

## Contexto

El PR 2492 impide enviar un expediente de Celiaquia cuando un menor queda sin
adulto responsable despues de eliminar el legajo del responsable. La revision
detecto tres brechas: la provincia no podia reactivar el responsable mediante
la recarga, la validacion aceptaba cuidadores con rol o edad invalidos y una
baja concurrente podia completarse despues de confirmar el envio.

## Decision

### Reactivacion por importacion

La recarga de una fila cuyo beneficiario ya esta activo debe continuar
procesando los datos del responsable. Si el responsable tiene un legajo
eliminado logicamente en el mismo expediente, la importacion lo restaura en la
misma transaccion y vuelve a asegurar la relacion familiar. La restauracion se
realiza solo despues de validar la fila; una fila invalida no reactiva datos.

Se preservan el identificador, la auditoria y los objetos eliminados en cascada.
La reactivacion se informa separadamente de los legajos nuevos.

### Responsable valido

Un responsable satisface la regla de envio cuando:

- tiene un legajo activo en el mismo expediente;
- su rol es `responsable` o `beneficiario_y_responsable`;
- tiene 18 anos o mas.

Por compatibilidad, si falta la fecha de nacimiento se conserva la tolerancia
actual y no se bloquea el envio por edad desconocida.

### Concurrencia

El envio y la baja provincial toman un bloqueo de fila sobre el expediente con
el mismo orden de adquisicion. La baja vuelve a comprobar el estado y los
permisos dentro de su transaccion. Una solicitud autorizada mientras el
expediente estaba `EN_ESPERA` no puede eliminar un legajo despues de que otro
proceso confirme el envio.

## Alternativas descartadas

- Restaurar todas las coincidencias antes de validar el archivo: puede reactivar
  legajos desde filas invalidas.
- Crear un endpoint y una pantalla de restauracion: agrega superficie de UI y
  permisos cuando el flujo acordado es la recarga/importacion.

## Criterios de aceptacion

1. Eliminar un responsable, reimportar la misma fila y confirmar el envio deja
   nuevamente activo el mismo legajo responsable.
2. La reimportacion vuelve a asegurar la relacion responsable-beneficiario y no
   duplica legajos.
3. Un cuidador menor o con rol solo beneficiario no habilita el envio.
4. Un adulto con rol responsable o doble rol habilita el envio.
5. Un responsable sin fecha conserva la tolerancia existente.
6. Una baja provincial no puede ejecutarse si el expediente fue confirmado
   mientras la solicitud esperaba el bloqueo.
7. No se agregan migraciones ni dependencias.

## Validacion

- Tests dirigidos de importacion, validacion de edad, envio y eliminacion.
- Casos de limite de edad antes, durante y despues del cumpleanos, incluido
  nacimiento el 29 de febrero.
- `black`, `pylint` y `djlint` solo sobre los archivos modificados cuando
  corresponda.
- Suite de `celiaquia` antes de recomendar merge, si se autoriza su ejecucion.
