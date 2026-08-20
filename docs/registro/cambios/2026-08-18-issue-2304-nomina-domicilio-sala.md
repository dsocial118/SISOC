# Issue 2304: departamento jurisdiccional y sala en nómina CDI

- La nómina de niños incorpora un departamento jurisdiccional relacionado con el catálogo `DepartamentoIpi`, filtrado por la provincia del domicilio y validado en el servidor.
- Piso y departamento habitacional del domicilio permanecen opcionales y diferenciados del departamento jurisdiccional.
- Sala vuelve a ser una selección única con las seis opciones solicitadas; los valores legacy ya guardados se conservan para poder editarlos.
- El decil de CDI se muestra en modo lectura a partir del departamento seleccionado y no se duplica en la nómina.
