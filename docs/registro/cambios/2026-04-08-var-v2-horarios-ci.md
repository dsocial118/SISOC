# Fix horarios AJAX y CI en Var-V2

- Se desacopló el modal de horarios de `add_comisionhorario` para que edición y borrado sigan renderizando sus modales cuando los permisos se asignan por separado.
- Las altas, ediciones y borrados de horarios por modal ahora responden JSON en requests AJAX y preservan los errores de validación server-side en lugar de cerrar el modal y recargar siempre.
- Se ajustaron helpers y formato en VAT/core/templates para dejar la branch alineada con `black`, `djlint` y `pylint`.
