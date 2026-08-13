# Issue 2272: corrección controlada de expedientes

## Alcance

Se incorpora el comando de Django corregir_expedientes_issue_2272.
Su modo por defecto ejecuta solamente el preflight; la opción --apply requiere
una ventana sin altas ni ediciones de admisiones y actualiza en una transacción
los dos campos que representan el expediente:

- Admision.num_expediente (Técnicos).
- Admision.legales_num_if (Legales).

No modifica num_if, estados del proceso ni archivos PDF/DOCX ya generados.
Para trazabilidad, la aplicación crea entradas en AdmisionHistorial con usuario
nulo, ya que se trata de una corrección operativa automatizada.

## Guardas

El comando verifica el checksum normalizado por saltos de línea y encabezados
del CSV versionado, consolida sólo filas exactamente repetidas, valida el
formato vigente de #2076, rechaza expedientes repetidos entre admisiones y
verifica que los IDs existan en la base objetivo antes de escribir.

El manifiesto versionado deriva de `CORRECCIONES EXPEDIENTES - Hoja 2.csv`,
recibido el 2026-08-12. Contiene 470 admisiones, sin IDs ni expedientes
repetidos. Por instrucción funcional explícita se completaron con ceros a la
izquierda los 362 números que tenían siete u ocho dígitos, hasta llegar al
formato vigente de nueve dígitos.

Las admisiones 1448, 1794, 2314 y 2462, que formaban las dos colisiones de la
fuente anterior, no aparecen en la fuente nueva. No existe una regla especial
de exclusión: el comando actualiza solamente los IDs presentes en el manifiesto
y deja intactas las demás admisiones.

## Siguiente paso operativo

La fuente aprobada queda versionada junto con su checksum. No se acepta un
manifiesto externo con `--manifest`, para conservar la trazabilidad de la
fuente aplicada.

El procedimiento detallado para HML y producción, incluidos preflight,
verificación posterior y recuperación, está en
`docs/operacion/correccion_expedientes_issue_2272.md`. La restricción única de
base debe incorporarse después de limpiar los duplicados históricos verificados
en esos entornos.
