# Bloqueantes CDI — tercera ronda QA

## Alcance

Correcciones reproducidas a partir del reporte QA del 30/08/2026. La geografía
BAHRA queda fuera de este cambio hasta contar con la verificación independiente
de producción solicitada.

## Cambios funcionales

- La descarga provincial conserva sólo fichas activas, únicas y de hasta 48
  meses a la fecha de generación. Las fichas activas mayores de 48 meses se
  omiten incluso si un administrador decidió mantenerlas activas.
- En el legajo de niños, el CUIT/CUIL del Responsable 1 es obligatorio y la
  unidad de edad se calcula en servidor; un POST no puede elegirla manualmente.
- La pregunta obligatoria de apoyo al desarrollo aparece una sola vez, también
  en la edición AJAX. El campo histórico se conserva y se sincroniza sólo para
  fichas con discapacidad, respetando su invariante anterior.
- La oferta de servicios del CDI se presenta como casillas de selección
  múltiple, sin cambio de esquema.
- El alta EGP específica queda como redirección de compatibilidad al ABM general
  de usuarios. El ABM y la importación aceptan una o más provincias completas
  para el grupo `SIMEPI - EGP`.
- Los grupos `SIMEPI - Administrador` y `SIMEPI - Equipo Nacional` pueden buscar
  y visualizar el listado completo. La edición continúa aplicando el alcance
  delegable para evitar elevación de privilegios; la exportación CSV tampoco
  amplía ese alcance.
- Una migración correctiva vuelve a archivar el comunicado interno publicado
  cuyo título comienza con `Importación de nómina`, por si fue creado o
  republicado después de la migración original.

## Compatibilidad y seguridad

- No se modifica ni elimina ningún dato geográfico.
- La URL EGP anterior no crea usuarios: redirige al formulario canónico y
  conserva su control de autorización.
- La visualización nacional ampliada no amplía el queryset de edición, baja o
  activación de usuarios.
- Los datos históricos de apoyo siguen disponibles mediante una representación
  unificada en el detalle.
- La edición completa y el re-render ante un POST inválido conservan todos los
  campos visibles cargados, incluidos geografía dependiente, multiselecciones,
  Responsable 2, ANSES y las 14 vacunas. El POST inválido no modifica la ficha.

## Validación local

- 369 tests focales aprobados y 1 omitido por condición del entorno para PDF,
  formularios CDI/Nómina, precarga integral al editar, conservación integral
  ante errores, vigencia única, alta de trabajador, usuarios, alta EGP legacy y
  migración de Comunicados.
- `black --check` y `djlint --check` sin cambios pendientes; `pylint` focal
  10/10; `makemigrations --check --dry-run` sin cambios de modelo pendientes.
- La validación en HML requiere promoción y despliegue separados; este cambio no
  prueba por sí mismo disponibilidad en HML.
