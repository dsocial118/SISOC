# 2026-08-06 - Puerto de auditoría de autenticación PWA

## Contexto

Las vistas de autenticación de `users` importaban el modelo y el servicio de
auditoría de PWA para persistir login, logout y consulta de contexto.

## Decision

`users.auth_audit` define los eventos de autenticación y un puerto estricto de
auditoría. PWA registra su persistidor existente durante `PwaConfig.ready()`.

## Consecuencias

- `users.api_views` deja de importar PWA.
- Los eventos, resultados y campos de auditoría existentes se conservan.
- La ausencia de persistidor falla de forma explícita; no se degrada a una
  pérdida silenciosa de auditoría.
- Se retiran dos excepciones runtime de `.importlinter`.

## Validacion

- `black --check users/auth_audit.py pwa/auth_audit.py users/api_views.py pwa/apps.py tests/test_auth_audit_port_unit.py pwa/test_auth_audit.py`.
- `pytest tests/test_auth_audit_port_unit.py pwa/test_auth_audit.py tests/test_pwa_auditoria_auth_api.py -q`.
- `python manage.py check`.
- `lint-imports`.
