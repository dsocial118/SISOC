# CLAUDE.md

Instrucciones específicas para Claude en este repo.

Fuente de verdad: `AGENTS.md`.

## Hard gate de lectura (importante)

Antes de implementar cambios, Claude debe:

1. Leer `AGENTS.md`.
2. Tomarlo como regla principal.
3. Luego complementar con `docs/ia/*` según la tarea.

Si el entorno no cargó `AGENTS.md` automáticamente, Claude debe abrirlo manualmente.
Si no puede leer `AGENTS.md`, debe:
- declararlo explícitamente,
- aplicar el fallback de este archivo,
- evitar decisiones amplias de arquitectura o refactors grandes hasta tener contexto.

## Orden de lectura recomendado

1. `AGENTS.md`
2. `docs/ia/STYLE_GUIDE.md`
3. `docs/ia/ARCHITECTURE.md`
4. `docs/ia/TESTING.md`
5. `docs/ia/SECURITY_AI.md` / `docs/ia/ERRORS_LOGGING.md` si el cambio toca auth, datos o logs

## Fallback mínimo (si `AGENTS.md` no está disponible)

Reglas críticas a aplicar igual:

- No inventar contratos, modelos, campos, endpoints ni permisos.
- Mantener diffs pequeños y revisables.
- No mezclar feature + refactor + formateo masivo.
- Compatibilidad hacia atrás por defecto.
- No modificar tooling/CI/settings sin pedido explícito.
- Agregar tests mínimos (y regresión en bugfixes cuando sea viable).
- No exponer secretos/PII en logs/tests/ejemplos.
- Proponer mejoras cercanas solo como propuesta, sin implementación fuera de alcance sin aprobación.
- No asumir Celery/colas/workers: **actualmente no se usa Celery**.

Si falta información clave, explicitar supuestos concretos y limitar el alcance.

## Cómo trabajar bien en SISOC (Claude)

## 1) Confirmar contexto antes de proponer cambios

- Revisar el código real del módulo (views, models, services, tests).
- Buscar patrones existentes en la app antes de crear uno nuevo.
- Si falta información, explicitar supuestos concretos.
- No asumir infraestructura async tipo Celery; validar patrón real del repo primero.

## 2) Mantener cambios pequeños y revisables

- Preferir diffs enfocados.
- Evitar refactors amplios no solicitados.
- No mezclar limpieza masiva con cambios funcionales.

## 3) Estructura de entrega esperada

Responder con:
- Qué cambió.
- Archivos tocados.
- Validación ejecutada (tests/lint/format).
- Supuestos y límites.
- Riesgos o impactos.
- `Mejoras cercanas detectadas (opcional)`.

## 4) Seguridad y PII

- No hardcodear secretos.
- No exponer tokens/credenciales/PII en logs, tests o ejemplos.
- Respetar permisos y autenticación existentes.

## 5) Mejoras cercanas (solo propuesta)

Claude puede señalar mejoras cercanas al código tocado (tests faltantes, validación, logging, manejo de errores), pero no debe implementarlas fuera de alcance sin aprobación explícita.

## Checklist de cierre (Claude)

- Revisé `AGENTS.md` y docs de `docs/ia/` relevantes.
- Si no pude leer `AGENTS.md`, lo declaré y apliqué fallback mínimo.
- No inventé contratos ni estructuras inexistentes.
- Mantuve compatibilidad hacia atrás por defecto.
- Agregué tests mínimos o expliqué la limitación.
- Declaré supuestos explícitos.
- Reporté mejoras cercanas sin generar scope creep.

## Ejemplo de pedido (Claude)

```md
Refactor seguro en `core/views.py` para extraer validación repetida de filtros favoritos.
Sin cambiar comportamiento.
Agregá tests si detectás huecos críticos.
Si ves mejoras cercanas, listalas pero no las implementes sin aprobación.
```
