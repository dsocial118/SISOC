# 2026-09-15 - VPSL: equivalencia de nombres de CABA en sedes de itinerarios

La selección de sedes tentativas y localidades para un itinerario en Ciudad Autónoma de Buenos Aires acepta jurisdicciones guardadas como `Ciudad Autónoma de Buenos Aires` o `Ciudad de Buenos Aires`. La validación del alta usa el mismo criterio, por lo que también permite guardar una sede histórica con el segundo nombre.

La equivalencia es simétrica si el registro de Provincia usa cualquiera de los dos nombres. Las demás provincias conservan coincidencia exacta; en particular, una sede de `Buenos Aires` no se incluye en CABA y viceversa. La regla vive en `ver_para_ser_libre/services/sedes.py` y es compartida por el formulario, el autocomplete y el filtro de localidades.

Validación: test acotado de creación de itinerarios con ambas jurisdicciones en `ver_para_ser_libre/tests/test_workflow.py`.
