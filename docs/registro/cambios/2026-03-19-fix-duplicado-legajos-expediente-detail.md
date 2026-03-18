# Fix duplicado de legajos en detalle de expediente (Celiaquía)

Fecha: 2026-03-19

## Contexto
En `celiaquia/expedientes/<pk>/`, algunos legajos se mostraban duplicados con el mismo ID luego de crear/importar.

## Causa raíz
En `ExpedienteDetailView.get_context_data`, los legajos clasificados como `hijos_sin_responsable` se agregaban a `legajos_enriquecidos`, pero no se marcaban como ya agregados en el set `agregados`.

Luego, en el bucle de “legajos huérfanos”, se volvían a insertar por no estar presentes en `agregados`, generando duplicados en memoria/render.

## Cambio aplicado
- Se reemplazó el `extend(hijos_sin_responsable)` por un agregado controlado:
  - solo se agrega si `ciudadano_id` no está en `agregados`;
  - al agregar, se registra en `agregados`.

Esto mantiene la lógica de inclusión de huérfanos reales y evita duplicación de legajos ya mostrados.

## Prueba de regresión
Se agregó `celiaquia/tests/test_expediente_detail.py` con un caso de un legajo sin responsable que verifica que en `response.context['legajos_enriquecidos']` aparezca una sola vez.
