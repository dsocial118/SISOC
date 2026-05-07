# Celiaquia - Auditoria de Excel masivo

## Contexto

La carga masiva de expedientes de Celiaquia conserva el archivo original en
`Expediente.excel_masivo`, pero no exponia de forma operativa quien lo cargo ni
cuando se proceso por ultima vez.

## Cambio

- Se agregan metadatos persistentes para el Excel vigente del expediente:
  usuario y horario de carga, usuario y horario de procesamiento.
- Admin y coordinador de Celiaquia pueden ver esos datos y descargar la copia
  del Excel original desde el listado y el detalle del expediente.
- En el detalle del expediente, la descarga queda disponible como accion
  superior con el boton "Descargar Excel Provincia".
- Provincia y tecnico conservan el flujo actual, sin acceso a esta auditoria ni
  a la descarga de la copia.

## Alcance

El cambio audita solo el Excel vigente del expediente. No crea historial de
reemplazos de archivos.
