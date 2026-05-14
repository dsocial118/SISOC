# Filtro "Estado de Revisión" en `/ciudadanos/listar`

## Qué cambió

- Se agregó el filtro `Estado de Revisión` en la grilla de `/ciudadanos/listar`.
- El filtro ofrece las opciones `Finalizada`, `Pendiente` y `Todos`, en ese orden.
- La opción por defecto es `Finalizada`.
- El filtro `Tipo de registro` pasó a mostrarse como `Estado identidad`.
- El filtro `Estado de Revisión` solo se muestra cuando `Estado identidad` es `Sin DNI`, `DNI no validado RENAPER` o `Todos`.
- La visibilidad del filtro se actualiza en cliente sin recargar la página.
- Cuando el filtro no aplica, se oculta conservando su espacio para que el botón `Aplicar` permanezca fijo al margen derecho.
- Se ajustó el layout del bloque de filtros para que `Provincia`, `Estado identidad`, `Estado de Revisión` y `Aplicar` queden en una sola línea en desktop.
- Se ajustó la escucha de eventos del selector de `Estado identidad` para que la ocultación/muestra del filtro sea más inmediata en cliente.

## Regla aplicada en la grilla

- `Pendiente`: filtra ciudadanos con `requiere_revision_manual=True`.
- `Finalizada`: filtra ciudadanos con `requiere_revision_manual=False`.
- `Todos`: no restringe por estado de revisión.

## Regla de búsqueda por `q`

- Cuando el usuario busca por `q`, el default implícito `Estado de Revisión = Finalizada` no debe ocultar coincidencias.
- En búsquedas por `q`, el filtro de revisión solo se aplica si el usuario eligió `Pendiente` o `Finalizada` explícitamente.
- Si `Estado de Revisión` no fue seleccionado de forma explícita, la búsqueda por `q` se comporta como `Todos`.

## Alcance y resguardo

- El cambio se limitó al listado y sus filtros.
- No se modificó la lógica de negocio que decide cuándo un ciudadano entra o sale de revisión manual.
- Si se intenta enviar `estado_revision` junto con un `Estado identidad` no habilitado, el backend ignora ese filtro.

## Validación

- Se validó el comportamiento con pruebas de `views` y templates de `ciudadanos` ejecutadas dentro de Docker.
- Comando ejecutado:

```powershell
docker compose -f BACKOFFICE\docker-compose.yml exec -T django pytest tests/test_ciudadanos_views_unit.py tests/test_ciudadanos_templates_unit.py -q
```

- Resultado final: `23 passed`.
