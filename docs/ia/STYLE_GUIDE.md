# STYLE_GUIDE.md

Guía de estilo y convenciones para generar código uniforme en SISOC.

Fuente de verdad general: `../../AGENTS.md`.

## Principios (obligatorios)

- Coherencia con el código existente del módulo.
- Cambios mínimos y locales.
- Legibilidad primero.
- No introducir patrones nuevos si ya existe uno aceptado en esa app.

## Naming (Python)

## Reglas básicas

- Módulos/archivos: `snake_case.py`
- Clases: `PascalCase`
- Funciones/métodos: `snake_case`
- Variables: `snake_case`
- Constantes: `UPPER_CASE`

## Naming del dominio (regla del equipo)

- Variables técnicas generales: inglés (`request_data`, `cache_key`, `response_data`).
- Nombres del dominio de negocio: conservar español si ya existe en modelos/flows (`comedor`, `relevamiento`, `admisiones`, `monto_prestacion`).
- No traducir nombres ya establecidos de campos/modelos/URLs.

Ejemplos correctos:
- `comedor_id`, `request_data`, `filtro_config`
- `monto_prestacion`, `fallback_response`

## Naming de endpoints (web/API)

- Mantener consistencia con el módulo y el dominio existente.
- Paths y parámetros deben reflejar nombres reales del dominio (`comedor_id`, `admision_id`).
- No renombrar endpoints existentes por estética.
- En endpoints nuevos, preferir nombres explícitos sobre abreviaturas ambiguas.

Ejemplos:
- `/api/comunicados/comedor/{comedor_id}/`
- `reverse(\"montoprestacion_detalle\", kwargs={\"pk\": pk})`

## Naming de hooks/components (solo si existe frontend JS/React en el cambio)

Este repo hoy es principalmente Django templates + JS, pero si el cambio incorpora frontend moderno:

- Hooks: `useXxx` (`useComedorFilters`, `useNominaFetch`)
- Componentes: `PascalCase` (`ComedorTable`, `FiltroFavoritoForm`)
- Props/estado: `camelCase` o convención del frontend existente del módulo (no imponer si no existe stack frontend formal)
- Separar nombres de dominio del payload técnico (`comedor`, `requestPayload`, `isLoading`)

## Imports (orden y consistencia)

Mantener orden consistente (como se ve en varios módulos del repo):
- Standard library
- Third-party
- First-party/local

Si el archivo ya usa comentarios de bloques de imports, conservar el estilo local.

## Compatibilidad con black (Python)

- Escribir pensando en `black` con `line-length = 88`.
- Si una línea tiende a crecer, partirla con paréntesis implícitos; no usar barras invertidas salvo que Python lo exija.
- Preferir trailing commas en estructuras multilínea para que `black` estabilice el formato.
- No alinear parámetros, diccionarios o asignaciones “a mano”.
- No preservar formato legacy si el bloque tocado queda claramente incompatible con `black`; corregir solo el bloque editado.

## Compatibilidad con pylint (Python)

- Tomar `.pylintrc` como contrato real, no como recomendación vaga.
- Naming por defecto:
  - funciones, métodos, variables y argumentos: `snake_case`
  - clases: `PascalCase`
  - constantes: `UPPER_CASE`
- Evitar nombres descartables salvo los ya aceptados por configuración (`i`, `j`, `k`, `pk`, `id`, `_`, `VAT`).
- Mantener imports agrupados por origen y evitar imports innecesarios o variables declaradas pero no usadas.
- Cuando `pylint` marca una violación, primero buscar una corrección de código: simplificar funciones, extraer helpers, mover lógica al boundary correcto, hacer más explícito el flujo o renombrar símbolos ambiguos.
- Evitar `# pylint: disable=...`, `# pylint: skip-file` y ampliaciones de ignore como salida por defecto. Si hay una falsa positiva o una restricción real del framework, usar la supresión más chica posible y dejar constancia en el cambio.
- Aunque `pylint` permite `max-line-length = 150`, para código nuevo/modificado se prioriza el límite práctico de `black` (`88`). Las líneas más largas deberían quedar reservadas a casos difíciles de partir limpiamente (URLs, strings fijas, regex, SQL, etc.).

## Tipado en Python (cuándo y cómo)

## Usar typing cuando aporta valor

Priorizar type hints en:
- servicios/utilidades nuevas,
- helpers reutilizables,
- funciones con payloads/retornos no triviales,
- código nuevo de parsing/normalización/transformación.

## No forzar tipado ceremonial en legado

- No agregar anotaciones masivas a módulos legacy si no mejora claridad.
- Agregar typing de forma incremental en el código que se modifica.

## Reglas prácticas

- Preferir tipos concretos cuando se conocen (`dict[str, Any]`, `list[str]`).
- Usar `Mapping`/`Iterable` para entradas genéricas.
- Usar `Optional[T]` cuando el `None` sea parte real del contrato.

## Docstrings y comentarios

- Docstrings en español, breves y descriptivas.
- Prioridad: servicios, vistas, modelos, management commands, helpers no obvios.
- Comentarios solo cuando aclaran una decisión o edge case.
- Evitar comentarios redundantes.

## Errores y mensajes

## Mensajes al usuario

- En español.
- Claros y accionables.
- Evitar mensajes técnicos internos en respuestas UI/API.

## Mensajes técnicos/logs

- Incluir contexto suficiente para depurar.
- No incluir secretos ni PII.
- Usar placeholders o contexto estructurado cuando aplica.

## Configuración y variables de entorno

- Leer config desde `settings` / variables de entorno, no hardcodear credenciales.
- Usar defaults explícitos cuando sea seguro.
- Validar entradas/config si el flujo depende de formatos específicos.

## Responsabilidades por tipo de archivo (Django/DRF)

## Views (Django / DRF views)

- Delgadas: orquestan request/response, permisos y delegan lógica.
- No concentrar lógica de negocio compleja en views.
- Validar entradas y devolver status codes coherentes.

## Services

- Lugar preferido para lógica de negocio reutilizable y reglas de orquestación.
- Mantener interfaces claras y predecibles.
- Evitar side effects implícitos no documentados.

## Serializers (DRF)

- Usar para shape/validación/serialización de datos API.
- Mantener views de API delgadas.
- Evitar lógica de negocio pesada que debería vivir en services.

## Forms (Django)

- Validación de input web y reglas de formulario.
- Reutilizar forms existentes si el flujo lo permite.

## Templates Django

- Evitar lógica compleja, consultas o branching excesivo.
- Preferir includes/parciales para fragmentos reutilizables.
- Mantener templates orientados a presentación.

## Compatibilidad con djlint (templates)

- Escribir templates con indentación de 4 espacios.
- Separar bloques `{% if %}`, `{% for %}`, `{% include %}` y contenido HTML de forma legible; `djlint` no debería necesitar reestructurar todo el bloque.
- No compactar atributos o contenido en una sola línea si el largo o los template tags ya anticipan wrapping.
- Preservar líneas en blanco solo cuando ayudan a separar bloques visuales; evitar espaciado arbitrario.
- Recordar que el formatter usa perfil `django`, preserva blank lines y tiene reglas ignoradas específicas en `.djlintrc`; no inventar reglas de estilo ajenas a esa configuración.

## DRF: convenciones prácticas

- Verificar permisos existentes (`IsAuthenticated`, API keys, etc.) antes de agregar endpoints.
- Usar `select_related` / `prefetch_related` cuando el endpoint serializa relaciones.
- Mantener compatibilidad del payload salvo pedido explícito.

## Código legado: cómo tocarlo sin romper el repo

- Mejorar localmente el bloque que se toca.
- No reformatear o renombrar masivamente por “limpieza”.
- Si hay deuda técnica cercana, reportarla como mejora opcional (no implementarla fuera de alcance sin aprobación).

## Ejemplos concretos

## Ejemplo A - helper de service (bueno)

```python
from typing import Any, Mapping


def normalizar_filtros(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normaliza filtros del request manteniendo defaults compatibles."""
    logic = str(payload.get("logic") or "AND").upper()
    if logic not in ("AND", "OR"):
        logic = "AND"
    items = payload.get("items") or []
    return {"logic": logic, "items": items}
```

## Ejemplo B - naming mixto (dominio + técnico)

```python
comedor_id = request.GET.get("comedor_id")
request_data = _parsear_datos_request(request)
cache_key = f"comedores:{comedor_id}:detalle"
```

## Ejemplo C - llamada preparada para black

```python
response = client.post(
    url,
    data={
        "comedor_id": comedor_id,
        "beneficiarios": beneficiarios,
        "observaciones": observaciones,
    },
)
```

## Ejemplo D - template preparado para djlint

```django
{% if comedor_activo %}
    <div class="alert alert-info">
        <span>{{ comedor_activo.nombre }}</span>
    </div>
{% endif %}
```
