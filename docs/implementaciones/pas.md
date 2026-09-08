# PAS: padrón, DDJJ e informes

## Alcance

La aplicación `pas` concentra el padrón de titulares, sus estados, avisos e
historial. Expone una fachada pública de datos sin devolver modelos o querysets
y conserva las operaciones de negocio en sus servicios.

La importación de declaraciones juradas usa tokens para evitar duplicados y
asociaciones cruzadas. Los informes son fotografías persistentes: una vez
generados no cambian aunque luego se modifique el padrón.

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
  de los permisos Django de consulta y generación del informe.

## Privacidad, permisos y rollback

Los informes pueden contener datos personales e históricos. La lectura del
padrón, la creación de informes y la descarga se autorizan por separado; no se
debe otorgar exportación por el solo hecho de permitir una consulta.

La migración `pas.0003_pasinforme` es aditiva. Revertirla elimina los informes
persistidos, por lo que los resultados que deban conservarse deben exportarse o
respaldarse antes del rollback.

## Puntos de entrada

- Modelos y servicios: `pas/models.py`, `pas/services/informe_service.py`.
- Formularios, vistas y rutas: `pas/forms.py`, `pas/views.py`, `pas/urls.py`.
- Contrato de datos entre dominios: `pas/api.py`.
- Contexto histórico: `docs/registro/cambios/2026-09-01-nucleo-pas.md` y
  `docs/registro/cambios/2026-09-01-informes-pas.md`.
