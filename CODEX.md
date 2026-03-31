# CODEX.md

Instrucciones específicas para Codex en este repo.

Fuente de verdad: `AGENTS.md`.

## Hard gate de lectura (importante)

Antes de implementar cambios, Codex debe:

1. Leer `AGENTS.md`.
2. Aplicar sus reglas como prioridad.
3. Leer `docs/indice.md` y luego `docs/ia/*` según el tipo de tarea.
4. Leer la documentación funcional/técnica del dominio afectado dentro de `docs/`.
5. Registrar cambios o decisiones importantes en `docs/` dentro de la subcarpeta que corresponda (crearla si no existe).

Si la integración no cargó automáticamente `AGENTS.md`, Codex debe abrirlo manualmente.
Si no puede acceder a `AGENTS.md`, debe:
- declararlo explícitamente en la respuesta,
- usar el bloque de fallback de este archivo,
- evitar cambios grandes o de alto riesgo hasta tener contexto.

## Orden de lectura recomendado

1. `AGENTS.md`
2. `docs/indice.md`
3. `docs/ia/CONTEXT_HYGIENE.md`
4. `docs/ia/STYLE_GUIDE.md`
5. `docs/ia/ARCHITECTURE.md`
6. `docs/ia/TESTING.md`
7. `docs/registro/README.md`
8. Archivos concretos del módulo a modificar y docs del dominio afectado

## Fallback mínimo (si `AGENTS.md` no está disponible)

Aplicar estas reglas como no negociables:

- No inventar APIs, modelos, campos, serializers, endpoints ni permisos.
- Hacer cambios mínimos (`small diffs`) y no mezclar feature + refactor + formateo masivo.
- Mantener compatibilidad hacia atrás por defecto.
- No tocar configs de tooling/CI/settings sin pedido explícito.
- Agregar tests mínimos en features nuevas y regresión en bugfixes cuando sea viable.
- No loggear secretos/PII y respetar permisos existentes.
- Leer documentación relevante en `docs/` antes de proponer cambios.
- Documentar decisiones/cambios importantes en `docs/<subcarpeta>/...` sin depender de herramientas específicas.
- Podés proponer mejoras cercanas, pero no implementarlas fuera de alcance sin aprobación.
- No asumir Celery/workers/colas: **actualmente no se usa Celery** en este repo.

Si falta contexto crítico, frenar expansión de alcance y pedir/explicitar supuestos.

## Forma de trabajo esperada (Codex)

## Entorno Docker aislado por worktree (obligatorio)

- En SISOC, Codex debe ignorar el Python del host y ejecutar Django/pytest únicamente dentro de Docker Compose.
- Cada worktree/tarea/agente debe usar su propio proyecto Compose aislado.
- El nombre del proyecto Compose se calcula desde el worktree actual en `scripts/ai/codex_common.ps1`.
- Toda llamada a Compose debe incluir `docker-compose.yml` + `docker-compose.codex.yml`; el override elimina puertos publicados para evitar choques entre agentes.
- Para comandos de validación o administración, preferir `run --rm` sobre `exec`.
- Punto de entrada recomendado:
  - `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 test`
  - `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 smoke`
  - `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 manage makemigrations --check --dry-run`
  - `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 manage migrate`

## 1) Explorar contexto rápido sin romper alcance

- Buscar implementaciones similares antes de editar.
- Revisar tests existentes del módulo para copiar patrón.
- Confirmar permisos, serializers, forms y services reales.
- Evitar suposiciones sobre modelos/campos sin verificar.
- Aplicar higiene de contexto: cargar primero archivos mínimos relevantes y expandir solo si hace falta (ver `docs/ia/CONTEXT_HYGIENE.md`).
- Podés usar `bash scripts/ai/preflight.sh <tipo> [path]` como preflight local opcional.

## 2) Decidir diff mínimo

Antes de editar, definir:
- cuál es el comportamiento a cambiar,
- cuál es el archivo responsable,
- cuál es el test mínimo que lo cubre.
- cuál es el check mínimo de formato/lint que confirma que el archivo nuevo sigue `black`, `pylint` y/o `djlint`.

Si el cambio requiere tocar muchos archivos, explicar por qué.

## 2.1) Escribir compatible con el tooling del repo

- Python: escribir `black-first`. Tomar `88` caracteres como referencia práctica y usar paréntesis implícitos antes que continuaciones manuales.
- `pylint`: respetar naming y estructura definidos en `.pylintrc`; no introducir variables ambiguas, imports fuera de orden ni argumentos innecesarios “porque después se arreglan”.
- Templates: escribir bloques y tags para que `djlint` necesite ajustes mínimos. Evitar HTML/Django comprimido en una sola línea cuando hay condicionales, loops o atributos largos.
- Antes de correr checks globales, ejecutar validaciones acotadas sobre los archivos editados siempre que el cambio lo permita.

## 3) Reportar cambios de forma útil

Al entregar, incluir:
- archivos tocados,
- comportamiento nuevo/corregido,
- validación ejecutada,
- supuestos,
- riesgos,
- registro en `docs/<subcarpeta>/...` para cambios/decisiones importantes (o motivo si no aplica),
- mejoras cercanas detectadas (opcional).

## 4) Tareas grandes: trabajar por fases

Para refactors/features grandes:
- dividir en fases incrementales,
- mantener el sistema funcional entre fases,
- separar cambios estructurales de cambios funcionales cuando sea posible,
- proponer el plan antes de expandir alcance.

## 5) Mejoras cercanas sin scope creep

Codex puede detectar mejoras cercanas, pero:
- no las implementa fuera de alcance sin aprobación,
- las reporta separadas,
- indica impacto y costo estimado.

Formato sugerido:

```md
## Mejoras cercanas detectadas (opcional)
- [Impacto alto | costo bajo] ...
```

## Heurísticas útiles para este repo

- Lógica de negocio suele vivir en `services/`.
- Views Django y DRF coexisten; validar patrón por app.
- Tests usan `pytest`, fixtures y `monkeypatch` con frecuencia.
- Templates usan `djlint`; evitar meter lógica compleja en HTML.
- Logging y errores tienen patrones ya implementados en `config/settings.py` y `core/utils.py`.
- No asumir Celery para tareas async; revisar `management/commands`, servicios o hilos existentes antes de proponer colas/workers.

## Checklist de cierre (Codex)

- Leí `AGENTS.md` y guías relevantes de `docs/ia/`.
- Si no pude leer `AGENTS.md`, lo declaré y apliqué fallback mínimo.
- Respeté higiene de contexto (sin abrir/cambiar archivos innecesarios).
- No inventé APIs/campos/modelos.
- Mantuve diff chico y enfocado.
- No toqué configs de tooling/CI sin pedido.
- Escribí código/templates ya alineados con `black`, `pylint` y `djlint`, evitando depender de un formateo correctivo masivo.
- Agregué tests mínimos o expliqué por qué no.
- Registré cambios/decisiones importantes en `docs/` (subcarpeta temática) o expliqué por qué no aplicaba.
- Declaré supuestos y riesgos.
- Reporté mejoras cercanas solo como propuesta.

## Ejemplo de pedido (Codex)

```md
Corregí el manejo de errores en `core/services/image_service.py` cuando la ruta es inválida.
Fix mínimo + test de regresión.
No refactorices el módulo completo.
Podés proponer mejoras cercanas sin implementarlas.
```
