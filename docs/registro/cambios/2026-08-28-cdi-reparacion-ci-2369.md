# Reparación de CI para correcciones CDI #2369

Fecha: 2026-08-28

## Alcance

- Las fixtures de alta y edición ahora representan días de funcionamiento obligatorios y menores de 48 meses cuando prueban estados distintos de Pendiente.
- Se incorpora la migración que persiste las etiquetas `No sabe` aprobadas en #2369.
- Se ajustan dos detalles internos para que pylint valide sin alterar el contrato de formularios.

## Validación

- 185 tests focalizados de formularios y vistas CDI en Docker.
- `makemigrations --check --dry-run` contra el runtime Docker: sin cambios detectados.
- `pylint centrodeinfancia/forms.py` en Docker: 10.00/10.
