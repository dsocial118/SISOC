# Informes técnicos: retiro de Monto total conveniado

Referencia: issue #2403, comentario de jcamiloparra del 2026-09-08
https://github.com/dsocial118/SISOC/issues/2403#issuecomment-5589651567.

Se elimina la sección del formulario compartido de informes técnicos base y
jurídico (creación y edición). Los dos campos de monto dejan de formar parte
del formulario, tanto en borrador como al finalizar, con financiamiento vigente
o finalizado. Se evita así dejar una validación obligatoria sin campo visible.

Los campos del modelo, valores históricos y variables documentales permanecen
disponibles. No se modifican plantillas publicadas, permisos ni el monto del
convenio PNUD del legajo de comedor. No requiere migraciones.

Cobertura de regresión en `admisiones/tests/test_variables_documentales_renovacion.py`:
ausencia de campos y errores por montos en ambas variantes y estados de
financiamiento, y conservación de montos históricos al editar, incluso si el
POST intenta reemplazarlos.

Validación local: sintaxis Python y `git diff --check` correctos; ocho escenarios
aislados del helper real confirmaron la exclusión de los montos y la conservación
de las reglas de campos vecinos. También se comprobó la ausencia del bloque en
el template. Los tests Django no pudieron ejecutarse: la `.venv` disponible no
tiene `pytest` ni Django instalados. Pendiente en un entorno con dependencias:
`USE_SQLITE_FOR_TESTS=1 python -m pytest admisiones/tests/test_variables_documentales_renovacion.py -q`.

La validación completa de envío y generación documental depende del entorno
Django y de las plantillas publicadas. Para revertir, restaurar el bloque del
template y la configuración anterior de los campos; los datos se conservan.
