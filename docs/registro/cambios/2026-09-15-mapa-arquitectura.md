# Mapa de arquitectura: visor interno regenerado en cada arranque

Se agrega `/arquitectura/`, un mapa navegable de los módulos de SISOC, sus
dependencias reales, las PWA y las integraciones externas. El grafo se extrae
del repositorio, no se escribe a mano: apps de `INSTALLED_APPS`, prefijos de
`config/urls.py`, señales de autenticación de cada API, imports entre apps por
AST, el árbol de `templates/includes/sidebar/opciones.html` con sus permisos, y
`scripts/operacion/pwas.json`.

Se accede desde Novedades, con un botón junto al badge de última actualización.
La vista exige sesión iniciada; no hay permiso dedicado. Es una decisión
consciente del equipo: el objetivo es que la arquitectura sea transparente para
los interesados. Implica que cualquier usuario del sistema —incluidos perfiles
externos al organismo— puede ver nombres de permisos, rutas montadas y
estructura de módulos. Si eso deja de ser aceptable, el cambio es acotado:
agregar un permiso al decorador de `mapa_arquitectura_view` y de
`mapa_arquitectura_datos`.

## Dónde vive cada cosa

`static/arquitectura/mapa.css` y `mapa.js` son **fuente versionada** del visor,
no salidas del generador. Van como estáticos porque el CSP de producción no
admite `<style>` ni `<script>` inline (`config/middlewares/csp.py`).

El grafo se escribe en `var/arquitectura/grafo.json`, ignorado por git, por dos
razones independientes:

1. **No puede ir en `static/`.** Nginx publica `/static/` por `alias` a
   `static_root/` sin pasar por Django, así que un `@login_required` en la vista
   no protegería el archivo. El grafo describe permisos, rutas y estructura
   interna. Lo entrega `mapa_arquitectura_datos`, que exige sesión.
2. **No puede ir en el checkout versionado.** El generador corre en cada
   arranque y su salida cambia siempre (lleva timestamp).
   `scripts/operacion/deploy_refresh.sh` aborta el despliegue si encuentra
   cambios locales en archivos tracked, así que escribir ahí habría bloqueado el
   deploy siguiente.

`docs/arquitectura/grafo_sisoc.json` y `mapa_sisoc.html` (documento de una sola
pieza, para leer el mapa fuera de SISOC) se actualizan sólo con
`python scripts/arquitectura/generar_mapa.py --docs`, a mano. El arranque no los
toca.

## Arranque

`docker/django/entrypoint.py` ejecuta `manage.py generar_mapa_arquitectura` al
inicio de `run_server()`, antes de `cache_busting()`. Los roles de worker
retornan antes y no lo ejecutan. Un fallo del generador se loguea y el arranque
continúa: el mapa es informativo y no debe tumbar el contenedor. El generador
tarda ~1,3 s sobre el repo actual y escribe de forma atómica (temporal más
`os.replace`), así que una interrupción no deja un JSON truncado que la vista
tomaría por válido.

## Hallazgo de arquitectura

Al escribir los tests del generador apareció una violación real del contrato
`core-no-domains`: `core/views.py:50` importa `historial.services.historial_service`.
`historial` está en `forbidden_modules` y no está en el baseline de
`ignore_imports`. import-linter no la detecta por la limitación que el propio
`.importlinter` documenta: grimp sólo analiza paquetes con `__init__.py`, y
`historial/services/` es un namespace package. El agujero alcanza a todos los
namespace packages del repo.

El import **no se tocó** en este cambio. Queda documentado en
`tests/test_mapa_arquitectura_generador.py::test_ve_dependencias_que_import_linter_no_puede_ver`,
que falla si alguien lo corta o si el linter empieza a verlo. Decidir entre
cortarlo o agregarlo al baseline queda pendiente.

## Cobertura

- `tests/test_mapa_arquitectura_generador.py`: caracteriza el generador. El
  parser del sidebar usa regex sobre un template; si alguien lo reformatea no
  explota, devuelve datos incompletos en silencio y el mapa pasa a mentir. Los
  tests fijan el conteo de grupos, rutas de menú conocidas, herencia de permisos
  por `{% if %}` anidados, detección de los planos de autenticación y la
  ausencia del grafo en `static/`.
- `tests/test_mapa_arquitectura_smoke.py`: `/arquitectura/` redirige sin sesión y
  responde 200 con sesión.
- `tests/test_docker_entrypoint_unit.py`: se actualizó
  `test_run_server_usa_gunicorn_en_entornos_deploy`, que exigía exactamente una
  llamada a `run_command`; ahora verifica el orden `mapa_arquitectura` →
  `gunicorn`. Se agregó un caso de fallo del generador que no aborta el arranque.

## Validación

Generador ejecutado sobre el repo: 34 apps, 131 dependencias entre apps (16 por
fachada `<app>.api`, 115 por imports de internals), 60 entradas de menú.
`pylint -E` en 10/10 y `compileall` limpio sobre lo tocado. Las aserciones de
`test_mapa_arquitectura_generador.py` se ejecutaron fuera de pytest porque el
`conftest.py` del repo importa DRF y el entorno local no tiene el stack: las doce
pasan.

Pendiente en un entorno con dependencias:

```bash
docker compose exec django pytest tests/test_mapa_arquitectura_generador.py tests/test_mapa_arquitectura_smoke.py tests/test_docker_entrypoint_unit.py -v
docker compose exec django black scripts/ core/ tests/
```

En el primer arranque de QA conviene mirar el log de la etapa
`mapa_arquitectura`: si el contenedor no puede escribir `var/`, el mapa queda sin
generar y la vista muestra el estado vacío en lugar de romper.

## Límites conocidos del grafo

- Las flechas son imports directos. El acoplamiento por signals y por los
  registries de `core` (`sidebar_access`, `favorite_filters`,
  `detail_contributions`) no aparece.
- `rutas_api` sale vacío para `relevamientos`: el generador sólo lee los
  `include()` directos de `config/urls.py`, y relevamientos monta sus URLs de API
  internamente.
- Los permisos del menú son la unión de los gates de los `{% if %}` abiertos:
  mezclan `and` y `or`, así que indican qué permisos aparecen en el camino, no un
  requisito exacto.
- El consumo de API de cada PWA está declarado a mano en `CONSUMO_PWA`, con su
  evidencia y su nivel de certeza, porque los frontends viven en repositorios
  privados separados.

## Revertir

Quitar la ruta de `core/urls.py`, las dos vistas de `core/views.py`, el botón de
`templates/changelog.html` y la llamada de `docker/django/entrypoint.py`. No hay
migraciones ni cambios de datos. `var/` puede borrarse sin consecuencias.
