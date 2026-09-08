# CDI: asistencia sobre nómina

## Alcance

La asistencia del CDI deja de operar sobre trabajadores y pasa a registrar a
las personas de la nómina activa del centro.

## Reglas funcionales

- Solo la nómina activa participa de nuevas cargas.
- Una baja con asistencia para la fecha consultada permanece visible y
  editable como historial; una nómina pendiente no es elegible ni reaparece.
- Una fila sin presente/ausente elimina el registro de esa fecha.
- El calendario marca un día si contiene al menos una asistencia, sin
  distinguir presente de ausente ni requerir carga completa.

## Compatibilidad

`AsistenciaTrabajador` y sus datos no se modifican. La URL histórica de
asistencia de trabajadores redirige a la nueva asistencia de nómina.

## Riesgos operativos

La escritura valida el conjunto de nóminas en el servidor y se ejecuta en una
transacción para evitar cargas parciales. El endpoint de calendario hereda el
scope territorial y el permiso de edición del CDI.
