# AGENTS.md

Guía principal para IAs (Codex/Claude/GPT) que trabajen en este repositorio.

Objetivo: reducir variabilidad entre IAs y PRs, producir cambios chicos y revisables, y mantener consistencia técnica con el stack real de SISOC.

## Alcance

Aplica a:
- Bugfixes puntuales.
- Features chicas y medianas.
- Refactors seguros (sin cambio funcional).
- Features grandes (por fases).

No reemplaza documentación funcional o técnica profunda. Para detalle, usar `docs/` y las guías en `docs/ia/`.

## Política Spec-as-Source (obligatoria)

Para trabajar en SISOC con asistentes, la documentación en `docs/` es fuente de verdad operacional:

- Antes de proponer o implementar cambios, es obligatorio leer `docs/indice.md`, `docs/ia/` y la documentación del dominio afectado.
- Cada cambio y cada decisión importante debe quedar documentada en `docs/` dentro de la subcarpeta que corresponda al dominio/tema.
- No se busca depender de herramientas específicas de spec-driven development: la fuente de verdad son archivos Markdown versionados en el repo.
- Convención recomendada (no exclusiva):
  - `docs/registro/cambios/YYYY-MM-DD-<tema>.md`
  - `docs/registro/decisiones/YYYY-MM-DD-<tema>.md`
- Si la subcarpeta necesaria no existe, debe crearse dentro de `docs/`.

## Stack real del repo (resumen)

- Backend: `Python 3.11`, `Django 4.2`, `Django REST Framework`.
- Base de datos: `MySQL` (tests pueden usar `SQLite` en memoria según settings).
- Frontend: templates Django + HTML/CSS/JS + Bootstrap.
- API schema/docs: `drf-spectacular`.
- Infra local/CI: `Docker Compose`, GitHub Actions.
- Asincronía actual: **no se usa Celery**. Hay jobs/tareas vía comandos, hilos y procesos del propio stack Django cuando aplica.

## Tooling real detectado (obligatorio respetar)

- Formato Python: `black` (config en `pyproject.toml`).
- Lint Python: `pylint` (config en `.pylintrc`, con `pylint_django`).
- Templates: `djlint` (config en `.djlintrc`).
- Tests: `pytest`, `pytest-django`, `pytest-xdist`.
- CI: `.github/workflows/lint.yml` y `.github/workflows/tests.yml`.

No imponer como obligatorio si no fue pedido: `ruff`, `mypy`, `eslint`, `prettier` (no hay configuración formal activa para estos checks en el repo).

## Disciplina de formato y lint para IAs (obligatoria)

- Escribir Python compatible con `black` desde el inicio. La referencia operativa es `line-length = 88`; no usar el `max-line-length = 150` de `pylint` como excusa para dejar líneas largas evitables.
- Preferir construcciones que `black` resuelve bien: paréntesis implícitos, literales multilínea y llamadas partidas por argumentos. Evitar alinear manualmente, columnas “bonitas” o wraps ad hoc que después `black` desarma.
- Mantener imports en bloques consistentes: standard library, terceros y código local. No reordenar imports no relacionados fuera del archivo tocado.
- Escribir nombres, firmas y variables alineados con `.pylintrc`: `snake_case` para funciones/variables, `PascalCase` para clases y helpers privados con prefijo `_` cuando aplique.
- En templates, escribir HTML/Django template tags pensando en `djlint`: indentación de 4 espacios, tags anidados legibles y sin compactar bloques en una sola línea si el formatter los va a expandir.
- Validar primero sobre archivos modificados para reducir fricción y ruido. Escalar a checks más amplios solo si el impacto del cambio lo justifica o el pedido lo exige.

## Patrones críticos del repo (leer antes de proponer cambios)

- La lógica de negocio va preferentemente en `services/` (no en views/templates).
- Coexisten vistas Django (web) y DRF (`api_views.py` / viewsets). Verificar el patrón real de cada app antes de implementar.
- El proyecto ya tiene logging custom configurado en `config/settings.py` y utilidades en `core/utils.py` (no inventar un esquema paralelo).
- No asumir Celery/colas/workers: actualmente no se usa Celery.

## Comandos principales (copy-paste)

```bash
# Levantar entorno local

docker compose up
# alternativa usada en docs históricas

docker-compose up

# Tests

docker compose exec django pytest -n auto
docker compose exec django pytest -m smoke

# Formato / lint

black .
black --check . --config pyproject.toml
black path/al/archivo.py --config pyproject.toml
djlint . --configuration=.djlintrc --reformat
djlint . --check --configuration=.djlintrc
djlint templates/ruta.html --reformat --configuration=.djlintrc
pylint **/*.py --rcfile=.pylintrc
pylint app/archivo.py --rcfile=.pylintrc
```

## Reglas de comportamiento para IAs (obligatorias)

## 1) Buscar antes de escribir

- No inventar APIs, funciones, clases, modelos, campos, serializers, endpoints ni permisos.
- Buscar referencias reales en el repo antes de proponer o escribir código.
- Reutilizar patrones existentes del módulo/app que se toca.
- No asumir Celery/colas workers si no está explícitamente pedido (actualmente no se usa Celery en el repo).

## 2) Cambios mínimos y revisables

- Hacer `small diffs`: modificar solo lo necesario para cumplir el pedido.
- No mezclar en un mismo cambio: feature + refactor + formateo masivo.
- No hacer refactors amplios no solicitados.
- No tocar archivos no relacionados “porque estaban cerca” salvo justificación clara.

## 3) Compatibilidad hacia atrás por defecto

- Mantener compatibilidad hacia atrás salvo pedido explícito.
- Si hay una ruptura necesaria, explicitarla antes y documentar impacto.

## 4) Supuestos explícitos

- Si falta información, avanzar con supuestos razonables y declararlos explícitamente.
- Los supuestos deben quedar en el mensaje de entrega y/o PR/commit message sugerido.

## 5) Respetar tooling y configuración

- No modificar configuraciones de `black`, `pylint`, `djlint`, `pytest`, CI o settings de entorno sin pedido explícito.
- No reordenar/importar/formatear todo el repo para “dejarlo prolijo”.

## 6) Calidad de código esperada

- Escribir código profesional, simple, eficiente y mantenible.
- Priorizar claridad sobre cleverness.
- Mantener nombres y estructura coherentes con el módulo existente.

## 7) Idioma y naming (regla del equipo)

- Documentación, comentarios y mensajes al usuario: en español.
- Variables y nombres técnicos generales: preferentemente en inglés (`request_data`, `cache_key`).
- Nombres de dominio del sistema: conservar en español cuando ya forman parte del modelo/flujo (`comedor`, `admisión`, `relevamiento`, `monto_prestacion`).
- No traducir nombres de modelos/campos/URLs existentes.

## 8) Testing mínimo obligatorio

- Toda funcionalidad nueva debe incluir testing mínimo.
- Todo bugfix debe incluir test de regresión cuando sea viable.
- Si no se agrega test, explicar por qué.

## 9) Documentación y ejemplos

- Si cambia comportamiento observable, actualizar docs relevantes.
- Incluir ejemplo mínimo de uso cuando el cambio agrega interfaz nueva (endpoint, helper, comando, flujo).

## 10) Seguridad y datos

- No hardcodear secretos.
- No loggear credenciales, tokens ni PII.
- Respetar permisos/autenticación existentes.

## 11) Disciplina de documentación (spec-as-source)

- Es obligatorio leer documentación vigente en `docs/` antes de implementar.
- Es obligatorio registrar en `docs/` (subcarpeta temática) cada cambio o decisión importante del trabajo realizado.
- Si una tarea no requiere registro, se debe explicitar por qué en la entrega.

## Flujo de trabajo por tamaño de cambio

## Tamaño S (bugfix / feature chica)

- Cambiar solo archivos directamente implicados.
- Agregar test puntual (service/view/api).
- Validar con checks enfocados.
- Entregar diff corto y explicación concreta.

## Tamaño M (refactor seguro / feature mediana)

- Dividir en pasos internos (sin PRs gigantes).
- Mantener comportamiento actual y cubrir regresiones.
- Separar refactor de comportamiento si es posible.
- Documentar riesgos y supuestos.

## Tamaño L (feature grande)

- Trabajar por fases incrementales.
- Definir interfaces/boundaries antes de expandir implementación.
- Incluir pruebas por fase y actualización de docs.
- Evitar “big bang changes”.

## Regla de mejoras cercanas (nueva)

La IA puede detectar mejoras cercanas al área tocada (por ejemplo: test faltante, validación débil, logging insuficiente, naming inconsistente, bug probable).

Reglas:
- Puede proponerlas.
- No debe implementarlas fuera de alcance sin aprobación explícita.
- Si son indispensables para que el cambio solicitado funcione correctamente, puede incluirlas, pero debe explicarlo.

Formato sugerido en la entrega:

```md
## Mejoras cercanas detectadas (opcional)
- [Impacto alto | costo bajo] Falta test de regresión en `app/tests/...` para X.
- [Impacto medio | costo bajo] Validar `request.GET['...']` para evitar 500 en Y.
```

## Definition of Done (cambios hechos por IA)

Antes de cerrar una tarea, la IA debe verificar (o declarar por qué no pudo):

- Código implementado con diffs pequeños y coherentes con el alcance.
- Formato/lint/test ejecutados (o justificación si no se ejecutaron).
- Tests mínimos agregados cuando aplica.
- Test de regresión agregado en bugfix cuando aplica.
- Documentación actualizada si cambió comportamiento.
- Registro de cambios/decisiones importantes en `docs/<subcarpeta>/...` (o justificación explícita si no aplica).
- Supuestos y límites explicitados.
- Riesgos o follow-ups listados (si existen).

## Estructura de entrega recomendada (respuesta de la IA)

- Qué cambió.
- Archivos tocados.
- Validación ejecutada (tests/lint/format).
- Supuestos.
- Documento spec-as-source creado/actualizado en `docs/<subcarpeta>/...` (si aplica).
- Mejoras cercanas detectadas (opcional).

## Índice de guías especializadas (`docs/ia/`)

- `docs/ia/CONTRIBUTING_AI.md` - proceso de pedidos, PRs, commits, checks.
- `docs/ia/STYLE_GUIDE.md` - estilo de código y convenciones.
- `docs/ia/ARCHITECTURE.md` - organización del sistema y boundaries.
- `docs/ia/CONTEXT_HYGIENE.md` - higiene de contexto para asistentes locales (qué leer primero y qué evitar cargar).
- `docs/ia/TESTING.md` - estrategia de tests.
- `docs/ia/SECURITY_AI.md` - seguridad para cambios asistidos por IA.
- `docs/ia/ERRORS_LOGGING.md` - manejo de errores, excepciones y logs.

## How to ask the AI (plantillas cortas)

Usar estas plantillas para pedidos más consistentes. Adaptar paths y nombres reales del módulo.

## 1) Feature pequeña

```md
Quiero una feature chica en `[app]/[archivo]`.

Contexto:
- [qué flujo resuelve]
- [restricción de negocio]

Alcance:
- Cambiar solo [archivos o módulo]
- No refactorizar otras áreas

Criterio de aceptación:
- [comportamiento esperado]
- [caso borde importante]

Checks a correr:
- `docker compose exec django pytest -n auto [opcional: ruta específica]`

Podés proponer mejoras cercanas: sí/no
```

## 2) Bugfix

```md
Necesito un bugfix en `[path]`.

Bug actual:
- [qué pasa]
- [qué debería pasar]
- [pasos para reproducir si aplica]

Alcance:
- Fix mínimo, sin refactor masivo
- Mantener compatibilidad hacia atrás

Criterio de aceptación:
- [resultado esperado]
- Agregar test de regresión

Checks a correr:
- `docker compose exec django pytest -n auto [ruta de tests]`

Podés proponer mejoras cercanas: sí/no
```

## 3) Refactor seguro

```md
Quiero un refactor seguro (sin cambiar comportamiento) en `[path]`.

Objetivo:
- [legibilidad / duplicación / extraer helper / ordenar responsabilidades]

Restricciones:
- No cambiar contratos públicos
- No mezclar feature nueva
- Diff revisable

Criterio de aceptación:
- Tests existentes siguen pasando
- Si agregás tests, que sean puntuales

Checks a correr:
- `pylint **/*.py --rcfile=.pylintrc` (si impacta varias rutas)
- `docker compose exec django pytest -n auto [ruta]`
```

## 4) Agregar endpoint (Django/DRF)

```md
Quiero agregar un endpoint en `[app]`.

Tipo:
- Django view / DRF endpoint

Entrada/salida esperada:
- Request: [params/body]
- Response: [status + payload]

Restricciones:
- Respetar permisos/auth existentes
- Reutilizar services/serializers si ya hay patrón
- Agregar tests de permisos y caso feliz

Criterio de aceptación:
- [caso feliz]
- [caso inválido]
- [caso sin permiso]

Podés proponer mejoras cercanas: sí/no
```

## 5) Agregar componente/página (templates/JS)

```md
Quiero agregar una página/componente en templates Django.

Contexto:
- App/módulo: [app]
- Pantalla actual relacionada: [path]

Alcance:
- Reutilizar includes/parciales existentes si aplica
- Evitar lógica de negocio en template
- Mantener estilo visual actual

Criterio de aceptación:
- Render correcto
- Permisos correctos
- Tests mínimos si hay lógica en view/API asociada

Checks a correr:
- `djlint . --check --configuration=.djlintrc`
```

## 6) Agregar migración

```md
Necesito agregar una migración para `[app]`.

Cambio de modelo:
- [campo/índice/restricción]

Restricciones:
- Mantener compatibilidad de datos si aplica
- Evitar migraciones peligrosas sin explicar impacto
- Si hay data migration, que sea clara y reversible cuando sea viable

Criterio de aceptación:
- Migración consistente con el cambio
- Tests o validación mínima del comportamiento nuevo

Podés proponer mejoras cercanas: sí/no
```

## 7) Agregar test

```md
Quiero agregar tests para `[path o feature]`.

Objetivo del test:
- [regresión / permisos / validación / status code / rollback]

Alcance:
- Usar pytest + fixtures existentes
- Mockear integraciones externas si aplica
- No reescribir tests no relacionados

Criterio de aceptación:
- Cubre [casos]
- Falla sin el fix (si es regresión)

Comando sugerido:
- `docker compose exec django pytest -n auto [ruta de test]`
```

## Ejemplos rápidos (buen pedido)

## Ejemplo A - bugfix

```md
Corregí un 500 en `core/views.py` cuando `page` no es numérica en `load_organizaciones`.
Fix mínimo, sin refactor.
Agregá test de regresión en `core/tests/`.
Podés proponer mejoras cercanas, pero no implementarlas sin avisar.
```

## Ejemplo B - feature chica

```md
Agregá un filtro opcional por estado en el endpoint de comunicados de `comunicados/api_views.py`.
Reutilizá serializer actual si alcanza.
Incluí tests de caso feliz y parámetro inválido.
Mantener compatibilidad hacia atrás.
```

## Ver también

- `README.md`
- `docs/indice.md`
- `docs/contexto/arquitectura.md`
- `docs/contexto/dominio.md`
