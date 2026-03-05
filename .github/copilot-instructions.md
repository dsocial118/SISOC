# Instrucciones para GitHub Copilot (SISOC)

Estas instrucciones están alineadas con `AGENTS.md` y la documentación en `docs/ia/`.

## Fuente de verdad (obligatorio)

Copilot debe priorizar, en este orden:

1. `AGENTS.md` (reglas principales)
2. `docs/indice.md`
3. `docs/ia/CONTEXT_HYGIENE.md`
4. `docs/ia/STYLE_GUIDE.md`
5. `docs/ia/ARCHITECTURE.md`
6. `docs/ia/TESTING.md`
7. `docs/ia/SECURITY_AI.md` / `docs/ia/ERRORS_LOGGING.md` si aplica

Si `AGENTS.md` no fue cargado automáticamente por el entorno, usar estas instrucciones como fallback mínimo y evitar cambios grandes de arquitectura/refactor hasta tener contexto.

## Resumen del stack real

- Backend: `Python 3.11`, `Django 4.2`, `Django REST Framework`
- DB: `MySQL` (tests pueden usar `SQLite` en memoria)
- Frontend: templates Django + HTML/CSS/JS + Bootstrap
- Infra local/CI: Docker Compose + GitHub Actions
- Asincronía: **no se usa Celery** actualmente

## Patrones críticos del repo (no asumir otra cosa)

- La lógica de negocio va preferentemente en `services/`.
- Coexisten vistas Django (web) y DRF (`api_views.py` / viewsets); validar patrón por app.
- Hay logging custom en `config/settings.py` y `core/utils.py` (handlers/formatters propios).
- No imponer `ruff`, `mypy`, `eslint`, `prettier` como checks obligatorios (no hay config formal activa para esos checks).

## Reglas mínimas no negociables (fallback)

- No inventar APIs, modelos, campos, serializers, endpoints ni permisos.
- Hacer cambios mínimos (`small diffs`) y revisables.
- No mezclar feature + refactor + formateo masivo.
- Mantener compatibilidad hacia atrás por defecto.
- No tocar configs de tooling/CI/settings sin pedido explícito.
- Agregar tests mínimos en features nuevas y regresión en bugfixes cuando sea viable.
- No loggear secretos, tokens ni PII.
- Respetar permisos/autenticación existentes.
- Leer documentación relevante en `docs/` antes de proponer cambios.
- Documentar cambios/decisiones importantes en `docs/` dentro de subcarpeta temática (crearla si no existe).
- Podés proponer mejoras cercanas, pero no implementarlas fuera de alcance sin aprobación.

## Higiene de contexto (muy importante)

- Cargar primero el mínimo contexto suficiente y expandir solo si hace falta.
- Empezar por el archivo objetivo + tests del módulo + guías `docs/ia/*` relevantes.
- Evitar explorar apps no relacionadas o hacer limpieza oportunista.
- Si el repo está con cambios locales del usuario, no revertirlos ni asumir que son errores.

Ver: `docs/ia/CONTEXT_HYGIENE.md`.

## Comandos frecuentes (alineados al repo)

```bash
docker compose up
docker compose exec django pytest -n auto
docker compose exec django pytest -m smoke
black .
djlint . --configuration=.djlintrc --reformat
pylint **/*.py --rcfile=.pylintrc
```

## Calidad esperada de cambios

- Código profesional, simple y mantenible.
- Priorizar claridad sobre soluciones complejas.
- Reutilizar patrones existentes del módulo.
- Si falta información, explicitar supuestos.
- Si cambia comportamiento observable, actualizar docs relevantes.

## Entrega recomendada (cuando Copilot genere cambios asistidos)

- Qué cambió
- Archivos tocados
- Validación ejecutada (si se corrió)
- Supuestos
- Mejoras cercanas detectadas (opcional)
