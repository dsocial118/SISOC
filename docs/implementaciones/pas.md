# PAS: padrón, DDJJ e informes

## Alcance

La aplicación `pas` concentra el padrón de titulares, sus estados, avisos e
historial. Expone una fachada pública de datos sin devolver modelos o querysets
y conserva las operaciones de negocio en sus servicios.

La importación de declaraciones juradas usa tokens para evitar duplicados y
asociaciones cruzadas. Los informes son fotografías persistentes: una vez
generados no cambian aunque luego se modifique el padrón.

La importación CSV del padrón admite género mediante `Genero`,
`ciudadano_genero` o `ciudadano_genero_cod`, con valores `M`, `F` o `X`.
También conserva Calle y Altura por separado y mantiene el domicilio compuesto
por compatibilidad. La primera pantalla pública de la DDJJ edita Calle y Número
como campos independientes. En pantallas móviles, los banners superior e
inferior permanecen fijos y el desplazamiento ocurre únicamente dentro del
contenido central del formulario.

La DDJJ pública sigue el flujo de cinco pasos del prototipo UX. Las respuestas
afirmativas sobre embarazo y menores de 18 años despliegan sus preguntas de
controles dentro de la misma pantalla; al responder negativamente, esos campos
se ocultan y dejan de enviarse. Los textos visibles y el resumen final respetan
la terminología del prototipo, incluyendo `Número`, `compra de divisas` y
`Menores de 18 años a cargo`. El resumen incluye todas las respuestas emitidas,
incluidas las condicionales que correspondan. La presentación se confirma sin
solicitar ni almacenar una firma con el nombre completo.

## Informes reproducibles

`PasInforme` almacena los filtros, el modo y las filas serializadas de cada
consulta. El operador puede listar, previsualizar, consultar el detalle y
descargar el mismo resultado más tarde.

- La previsualización cuenta el universo completo, pero limita la
  serialización a 50 filas.
- Los filtros históricos distinguen el padrón vigente de los cambios de
  estado; no deben mezclarse ambos modos al interpretar un resultado.
- La exportación reutiliza la política central CSV UTF-8 con BOM y neutraliza
  prefijos de fórmula antes de entregar el archivo.
- Las descargas requieren el permiso transversal de exportación CSV, además
  de los permisos Django de consulta del padrón y del informe.

## Privacidad, permisos y rollback

Los informes pueden contener datos personales e históricos. La lectura del
padrón, la creación de informes y la descarga se autorizan por separado; no se
debe otorgar exportación por el solo hecho de permitir una consulta.

La migración `pas.0003_pasinforme` es aditiva. Revertirla elimina los informes
persistidos, por lo que los resultados que deban conservarse deben exportarse o
respaldarse antes del rollback.

La migración de datos `pas.0008_remove_ddjj_firma_respuestas` elimina de forma
irreversible la antigua clave `firma_nombre_completo` de las respuestas JSON de
DDJJ ya presentadas. Si ese dato histórico debiera conservarse fuera de PAS,
debe respaldarse antes de aplicar la migración.

## Puntos de entrada

- Modelos y servicios: `pas/models.py`, `pas/services/informe_service.py`.
- Formularios, vistas y rutas: `pas/forms.py`, `pas/views.py`, `pas/urls.py`.
- Contrato de datos entre dominios: `pas/api.py`.
- Contexto histórico: `docs/registro/cambios/2026-09-01-nucleo-pas.md` y
  `docs/registro/cambios/2026-09-01-informes-pas.md`.
