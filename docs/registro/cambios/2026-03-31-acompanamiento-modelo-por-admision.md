# Fase 1 — Modelo Acompanamiento por admisión (tk1273)

## Qué cambió

Se introdujo el modelo `Acompanamiento` en la app `acompanamientos` para permitir
múltiples acompañamientos por comedor, uno por cada admisión que llega al estado
correspondiente. Esto replica el patrón ya existente en `admisiones` (FK→Comedor).

## Archivos tocados

- `acompanamientos/models/acompanamiento.py` — nuevo modelo `Acompanamiento`;
  `InformacionRelevante` y `Prestacion` migradas de FK→Comedor a FK→Acompanamiento.
- `acompanamientos/models/hitos.py` — campo `acompanamiento` (nullable O2O) agregado
  a `Hitos`; campo `comedor` se mantiene por compatibilidad hacia atrás (se elimina en Fase 2).
- `acompanamientos/migrations/0004_acompanamiento_model.py` — migración de schema.
- `acompanamientos/migrations/0005_acompanamiento_data_migration.py` — data migration.
- `acompanamientos/admin.py` — registra `Acompanamiento`.

## Decisiones

- `Acompanamiento` usa `OneToOneField(Admision)` con `nro_convenio` copiado al momento
  de creación (campo fijo, no recalculado).
- `InformacionRelevante` y `Prestacion` no requirieron data migration (0 registros en producción).
- `Hitos.comedor` se conserva en esta fase para no romper consumidores existentes
  (`views.py`, `acompanamiento_service.py`, `comedores/services/comedor_service/impl.py`).
  Se limpiará en la Fase 2.

## Criterios de la data migration (Hitos)

| Grupo | Cantidad | Tratamiento |
|---|---|---|
| 1 admisión enviada | 357 | Vinculación directa |
| 2+ admisiones enviadas | 63 | Se vincula a la admisión más reciente (mayor id) |
| Huérfanos vacíos | 883 | Se dejan con acompanamiento=NULL |
| Huérfanos con datos | 11 | Se dejan con acompanamiento=NULL — pendiente resolución manual (Lead/PM) |

## Supuestos

- `Admision.numero_convenio` (CharField) es la fuente para `nro_convenio`; fallback a
  `convenio_numero` (IntegerField) si el primero está vacío.
- Los 11 hitos huérfanos con datos serán resueltos manualmente por el equipo antes
  o después del deploy, sin bloquear el avance de la feature.

## Fase 2 — Service layer (mismo commit)

- `acompanamientos/acompanamiento_service.py`:
  - `importar_datos_desde_admision` ahora recibe `admision` (antes `comedor`).
  - Crea `Acompanamiento` via `get_or_create`, vincula `InformacionRelevante` y
    `Prestacion` al nuevo modelo, y vincula/crea `Hitos` al `Acompanamiento`.
  - Retorna la instancia de `Acompanamiento` creada.
- `admisiones/services/admisiones_service/impl.py`:
  - `comenzar_acompanamiento` pasa `admision` en vez de `admision.comedor`.
- `tests/test_acompanamiento_service_helpers_unit.py`:
  - Test `test_importar_datos_desde_admision_ok_y_sin_admision` reescrito como
    `test_importar_datos_desde_admision_ok` para reflejar la nueva firma.

## Fase 3 — Views y template

- `acompanamientos/acompanamiento_service.py`:
  - `obtener_hitos` acepta `admision_id` opcional; busca primero por
    `acompanamiento__admision_id`, con fallback a `comedor` para registros pre-migración.
  - Nuevo método `obtener_admisiones_para_selector(comedor)`.
- `acompanamientos/views.py` (`AcompanamientoDetailView.get_context_data`):
  - Agrega al contexto: `admisiones_disponibles`, `admision_id_activa`,
    `tiene_multiples_activos`, `nro_convenio`.
  - Pasa `admision_id` a `obtener_hitos`.
- `acompanamientos/templates/acompañamiento_detail.html`:
  - Selector de convenios/admisiones (botones) con badge "Múltiples convenios activos".
  - Campo "Número de Convenio" en la sección Información Relevante.

## Fase 4 — Limpieza de Hitos.comedor

- `acompanamientos/models/hitos.py` — eliminado campo `comedor`; `__str__` actualizado.
- `acompanamientos/acompanamiento_service.py` — `crear_hitos` ahora busca el
  `Acompanamiento` activo más reciente del comedor. Si no existe, retorna sin hacer nada.
- `comedores/services/comedor_service/impl.py` — eliminados `_ensure_hito_para_comedor`,
  su llamada y los `messages` asociados. El `Hitos` se crea en `importar_datos_desde_admision`.
- `comedores/management/commands/update_comedores_dupla.py` — eliminada creación de
  `Hitos` por comedor e import huérfano.
- `acompanamientos/migrations/0007_hitos_cleanup_comedor.py` — borra hitos huérfanos
  (confirmado por el equipo que se puede perder esa data), elimina campo `comedor`.
- Tests actualizados: `test_crear_hitos_crea_subintervencion_y_nuevo_hito` y nuevo
  `test_crear_hitos_sin_acompanamiento_no_hace_nada`.
  `test_comedor_service_characterization_db.py` actualizado (sin assert de Hitos,
  `success_msg.call_count == 1`).
