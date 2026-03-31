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

## Fases siguientes

- **Fase 2:** actualizar `acompanamiento_service.py` y `admisiones_service.py`
  para crear `Acompanamiento` al llamar a `comenzar_acompanamiento()` y eliminar
  el uso de `Hitos.comedor`.
- **Fase 3:** actualizar views, URLs y templates para navegar por admisión/convenio.
- **Fase 4:** tests y limpieza de `Hitos.comedor`.
