# VAT: normativa compuesta en alta y edición de planes curriculares

- Se reemplazó la carga libre de `normativa` por tres campos en el formulario compartido de alta y edición: `tipo`, `número` y `año`.
- Los valores de tipo quedaron acotados a `Resolución` y `Disposición`.
- El año se ofrece como selector desde 1950 hasta el año actual.
- La persistencia sigue usando el campo existente `plan.normativa`, armado con el formato `<Tipo> <Número>/<Año>` cuando se carga solo la parte estructurada.
- Cuando se completa además una normativa libre, ambas variantes se serializan en el mismo campo para evitar migraciones y permitir reconstruir los cuatro valores en edición y detalle.
- Se agregó test para la creación con normativa compuesta y otro para prepopular la edición a partir de un valor ya guardado.
- Se corrigió la edición de planes con normativa solo estructurada para no reinyectar el mismo valor en el campo libre ni duplicarlo al guardar.
- Se alinearon las vistas de alta/edición/baja de planes con permisos explícitos por acción (`add/change/delete`) para usuarios provinciales.
