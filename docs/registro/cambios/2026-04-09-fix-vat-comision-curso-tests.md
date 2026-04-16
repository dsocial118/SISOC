# VAT - fix de detalle y alta de horarios en comision de curso

- Se corrigio `ComisionCursoHorarioCreateView` para que obtenga la URL de retorno despues de guardar la instancia, evitando el `AttributeError` por `self.object` inexistente durante `form_valid`.
- Se alinearon los tests de detalle de comision de curso con el URLconf real del proyecto para que el layout global resuelva correctamente las rutas de navegacion que usa el sidebar.
- Se mantuvo el comportamiento funcional esperado: al crear un horario, el sistema sigue generando sesiones automaticamente y el detalle sigue mostrando la gestion completa de la comision.
