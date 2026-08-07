# 2026-08-07 - Contrato público de Celiaquía

## Contexto

La Fase 0 retiró el import directo de `ciudadanos` a `celiaquia.models` al usar
un registro de contribuciones para Ciudadano 360. La contribución aún devolvía
un `QuerySet` y modelos al template, por lo que el detalle interno seguía siendo
un contrato implícito.

## Inventario

| Tipo | Módulo | Relación con Celiaquía |
| --- | --- | --- |
| Consumidor runtime | `ciudadanos.views` | Llama a `celiaquia.api.obtener_resumen_ciudadano(ciudadano_id)` para Ciudadano 360. |
| Composición de rutas | `config.urls` | Incluye `celiaquia.global_urls`; no importa views de Celiaquía. |
| Excepción de tooling | `scripts/debug_cruce.py` | Importa modelo y servicio para diagnóstico manual, fuera del runtime y del grafo analizado. |

Las dependencias salientes actuales de Celiaquía se mantienen sin cambios: sus
modelos dependen de `ciudadanos`, `core` y `core.soft_delete`; permisos y views
usan utilidades de `users`, `iam` y `core`; y la validación RENAPER consulta
`centrodefamilia.services`. Este issue fija su frontera de entrada, no refactoriza
esas dependencias internas existentes.

## Decisión

`celiaquia.api.obtener_resumen_ciudadano(ciudadano_id)` es la única operación
Python pública para el resumen de Celiaquía en Ciudadano 360. Recibe un ID y
devuelve dataclasses con valores de presentación ya resueltos; no acepta ni
retorna modelos Django, `QuerySet`, requests ni formularios.

`ciudadanos.views` conserva el permiso de la pantalla y captura el mismo error
de lectura que antes, pero solo conoce el DTO. `.importlinter` permite ese
import y prohíbe los módulos internos de Celiaquía a los demás dominios.

La ruta global `reporter-provincias/` queda bajo `celiaquia.global_urls` para
preservar URL, nombre y permiso sin que `config.urls` importe una view interna.

## Consecuencias

- No hay cambios de esquema, permisos, transacciones ni efectos laterales.
- El template usa campos estables del DTO en vez de atributos y métodos ORM.
- `import-linter` ahora incluye paquetes externos para analizar también
  `config`; tres puentes runtime preexistentes (`core.views -> historial` y
  dos imports de `ciudadanos` a `comedores`) quedan como baseline documentado,
  por lo que dependencias nuevas siguen rompiendo CI.
- `scripts/debug_cruce.py` sigue siendo tooling diagnóstico fuera del runtime y
  no forma parte de la API pública.

## Validación

- Tests de `celiaquia.api` y del helper de Ciudadano 360.
- `lint-imports`, incluyendo sondas temporales de imports prohibidos desde
  `ciudadanos` y `config` antes de publicar la PR.
- Regresión del reporter y smoke del detalle de ciudadano autenticado.
