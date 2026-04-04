# VAT: edición de centro sin edición de provincia

- En la pantalla `vat/centros/<id>/editar/` se oculta el campo `Provincia`.
- La edición conserva la provincia actual del centro aunque el formulario llegue sin ese valor en POST.
- Se mantiene sin cambios el comportamiento del alta, donde la provincia puede mostrarse si el usuario no la tiene en su perfil.