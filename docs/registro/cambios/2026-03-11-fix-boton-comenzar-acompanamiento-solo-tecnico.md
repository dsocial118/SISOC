# 2026-03-11 - Fix botón "Comenzar Acompañamiento" visible solo para técnico

## Contexto
- En el flujo de admisión de técnicos (`/comedores/admisiones/tecnicos/editar/<id>`), al finalizar la etapa de legales se mostraba el botón **Comenzar Acompañamiento** tanto para perfil técnico como para perfil abogado.
- Regla de negocio esperada: ese botón debe estar disponible únicamente para técnico.

## Cambios aplicados
- Se ajustó `admisiones/services/admisiones_service/impl.py` en el cálculo de botones disponibles:
  - `comenzar_acompaniamiento` ahora se agrega solo cuando el usuario resuelve como técnico (`es_tecnico=True`).
  - Se mantuvo sin cambios la visibilidad general de `rectificar_documentacion`.
- Se actualizaron tests de caracterización en `tests/test_admisiones_service_botones_characterization_db.py`:
  - Se corrigió la expectativa para usuarios sin roles (ya no deben ver `comenzar_acompaniamiento`).
  - Se agregó test de regresión específico para abogado validando que no vea `comenzar_acompaniamiento`.

## Impacto esperado
- Usuarios con rol abogado ya no verán el botón **Comenzar Acompañamiento** en admisiones técnicas.
- Usuarios con rol técnico mantienen el comportamiento existente para comenzar acompañamiento cuando corresponde.
- No cambia el contrato de endpoints ni la estructura del template.

## Validación
- `docker compose exec django pytest -q tests/test_admisiones_service_botones_characterization_db.py` → `13 passed`.

## Riesgos y rollback
- Riesgo bajo: ajuste acotado a lógica de visibilidad de botones del flujo de admisiones.
- Rollback: revertir cambios en:
  - `admisiones/services/admisiones_service/impl.py`
  - `tests/test_admisiones_service_botones_characterization_db.py`
