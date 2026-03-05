# ARCHITECTURE.md

Guía operativa de arquitectura y boundaries para cambios hechos por IA en SISOC.

Fuentes complementarias:
- `../../docs/contexto/arquitectura.md`
- `../../docs/contexto/dominio.md`
- `../../README.md`

## Resumen real del sistema (alto nivel)

- Monolito Django modular por apps de dominio.
- Web server-side con templates Django + Bootstrap/JS.
- APIs con DRF (`api_views.py`, serializers).
- Lógica de negocio distribuida en `services/` y utilidades por app.
- Persistencia con ORM Django sobre MySQL.
- Cache local (`LocMemCache`) configurada en settings.
- Logging custom configurado en `config/settings.py` con utilidades en `core/utils.py`.
- No se usa Celery actualmente (no asumir workers/colas salvo pedido explícito).
- Integraciones externas (p. ej. RENAPER/GESTIONAR) en servicios/tasks, no en templates.

## Capas y boundaries (regla de ubicación)

## 1) Presentación

Incluye:
- Django views (function-based y class-based views)
- DRF views / viewsets
- templates Django
- urls

Responsabilidad:
- Parsear request, permisos, validación superficial, delegar, serializar/responder.

No debería concentrar:
- lógica de negocio compleja,
- reglas de dominio reutilizables,
- integraciones externas extensas.

## 2) Negocio / aplicación

Ubicación preferida:
- `services/` por app
- helpers de dominio reutilizables
- managers/querysets cuando la regla es propia del acceso a datos

Responsabilidad:
- reglas de negocio,
- orquestación de operaciones,
- coordinación con modelos, cache e integraciones,
- manejo de edge cases del flujo.

## 3) Persistencia

- ORM Django (models/querysets/managers).
- Acceso a DB a través de modelos del dominio.
- Evitar SQL manual concatenado.

## 4) Infraestructura / integración

Incluye:
- integraciones HTTP externas,
- manejo de archivos,
- cache,
- logging,
- auth helpers,
- middleware.

Regla:
- encapsular detalles de integración fuera de views/templates.

## Dónde va la lógica de negocio (y dónde no)

## Sí va en `services/` cuando:

- La regla se reutiliza en varias views/endpoints.
- Hay múltiples pasos (DB + validación + side effects).
- Hay integración externa o cache.
- Hay parsing/normalización no trivial.

## No va en views/templates cuando:

- Requiere múltiples consultas y reglas de dominio.
- Se repite en varios endpoints/pantallas.
- Tiene side effects difíciles de testear.

## DRF: views vs serializers vs services

- Serializer: shape y validación de payload.
- ViewSet/APIView: permisos, querysets, orquestación fina.
- Service: reglas de negocio, side effects, integraciones, composición de operaciones.

## Patrones existentes del repo (usar antes de inventar)

Frecuentes en apps:
- `views.py` (web)
- `api_views.py` (DRF)
- `serializers.py` / `api_serializers.py`
- `forms.py`
- `services/`
- `signals.py`
- `management/commands/`
- `templatetags/`
- `tests/` y `conftest.py`

## Frontend (estado actual y regla si crece)

Estado actual predominante:
- Templates Django + parciales/includes + JS progresivo.

Regla actual:
- Mantener presentación en templates.
- Mover lógica de negocio a views/services.
- Si hay fetch/AJAX, encapsular validación y reglas en backend (view/serializer/service), no en template.

Si el cambio introduce frontend JS más estructurado (o React en un módulo puntual):
- Separar componentes presentacionales de contenedores/orquestadores.
- Hooks para estado/fetch (si existe React), no lógica de negocio de dominio.
- El backend sigue siendo fuente de verdad para permisos, validaciones y reglas de negocio.

## Side effects (tratar explícitamente)

Cuando un cambio toca side effects, documentar y testear:
- `signals` (post_save/pre_save/etc.)
- cache invalidation
- integraciones externas
- logging / auditoría
- archivos/media

Regla:
- no introducir side effects “silenciosos” sin dejarlo visible en código/tests.

## Integraciones externas (RENAPER/GESTIONAR y similares)

- Ubicarlas fuera de views.
- Mockearlas en tests.
- Manejar errores y timeouts con fallback/logs claros.
- No exponer detalles internos al usuario final.

## Seguridad y permisos (boundary transversal)

- Respetar autenticación/permisos existentes.
- Verificar grupos/permisos en views/endpoints nuevos.
- No abrir endpoints por default.

(Ver `./SECURITY_AI.md` para reglas detalladas.)

## Cómo encarar cambios grandes por fases

## Tamaño S

- 1 cambio funcional.
- 1 test puntual.
- 1 PR.

## Tamaño M

- Separar refactor seguro de cambio funcional si es posible.
- Agregar regresiones y cobertura de edge cases.
- Documentar riesgos.

## Tamaño L

- Definir fases con entregables intermedios.
- Mantener compatibilidad entre fases.
- Incluir migraciones y rollout/rollback si aplica.
- Actualizar docs en cada fase si cambia comportamiento.

## Ejemplos de ubicación (concretos)

## Ejemplo A - nuevo filtro de negocio reutilizable

- Si lo usan varias pantallas/endpoints: crear/expandir `services/...`.
- La view solo lee params, llama al service y responde.

## Ejemplo B - validación de payload API

- Validación de formato/campos: serializer DRF.
- Regla de negocio que consulta DB y dispara side effects: service.
