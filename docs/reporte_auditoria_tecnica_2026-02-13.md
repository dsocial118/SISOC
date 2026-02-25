# Auditoría técnica del repositorio BACKOFFICE

Fecha: 2026-02-13

## Alcance y método
Se relevó el repositorio completo (código Python/JS, tests, templates, configuración y docs) con revisión estática y comandos automatizados (`rg`, `pytest`, `vulture`, análisis AST para funciones largas y detección de duplicados por hash).

## Hallazgos

### 1) Código muerto / no ejecutado

1. **`tests/test_clasificacion/test_clasifiacion_comedor_service_puntuacion_0.py`**  
   - **Problema**: El archivo está completamente comentado; no define tests ejecutables.  
   - **Impacto**: Cobertura falsa/ruido; parece que existe validación pero no se ejecuta nada.  
   - **Sugerencia**: Eliminar el archivo o reactivar el test real con fixtures parametrizadas.

2. **`tests/test_clasificacion/test_clasifiacion_comedor_service_puntuacion_56.py`**  
   - **Problema**: Mismo patrón: todo comentado.  
   - **Impacto**: Misma deuda de pruebas “fantasma”.  
   - **Sugerencia**: Consolidar con un único test parametrizado (`[0, 56]`).

3. **`tests/test_clasificacion/crear_test_relevamiento.py`**  
   - **Problema**: También completamente comentado.  
   - **Impacto**: Helper de test no operativo, confunde mantenimiento.  
   - **Sugerencia**: Borrar o convertir en fixture viva (`conftest.py` del módulo).

4. **`admisiones/services/informes_service.py` y `admisiones/services/legales_service.py`**  
   - **Problema**: Imports no usados (`TemplateDoesNotExist`, `tempfile`) detectados con `vulture --min-confidence 90`.  
   - **Impacto**: Ruido, deuda menor de mantenibilidad.  
   - **Sugerencia**: Quitar imports no usados y agregar linter gate en CI.

5. **`celiaquia/views/comentarios_ejemplo.py`**  
   - **Problema**: Archivo de “ejemplo” sin referencias de uso en routing principal (sospecha de residual).  
   - **Impacto**: Superficie de código innecesaria.  
   - **Sugerencia**: Confirmar con negocio si se usa; si no, remover.

### 2) Duplicación o lógica casi duplicada

6. **`tests/test_clasificacion/test_clasifiacion_comedor_service_puntuacion_0.py`, `tests/test_clasificacion/test_clasifiacion_comedor_service_puntuacion_56.py`, `tests/test_clasificacion/crear_test_relevamiento.py`**  
   - **Problema**: Contenido idéntico (hash idéntico).  
   - **Impacto**: Mantenimiento triple y mayor probabilidad de drift.  
   - **Sugerencia**: Reemplazar por un único test parametrizado + helper en fixture.

7. **`organizaciones/templates/aval_confirm_delete.html` y `organizaciones/templates/firmante_confirm_delete.html` (también idéntico a `centrodefamilia/templates/centros/centro_confirm_delete.html`)**  
   - **Problema**: Plantillas de confirmación duplicadas literal.  
   - **Impacto**: Coste de mantener cambios UI consistentes.  
   - **Sugerencia**: Extraer parcial/base reutilizable con bloques de texto variables.

8. **`templates/includes/base.html` y `templates/includes/new_base.html`**  
   - **Problema**: Ambos contienen múltiples `FIXME` sobre scripts no localizados; indicio de duplicación/solapamiento de responsabilidades.  
   - **Impacto**: Riesgo de divergencia entre layouts base.  
   - **Sugerencia**: Definir un único layout canónico y mover scripts por página con bloques explícitos.

### 3) Funciones/métodos muy grandes (>200 líneas)

9. **`celiaquia/services/importacion_service.py::importar_legajos_desde_excel` (~939 líneas)**  
   - **Problema**: Método monolítico.  
   - **Impacto**: Muy difícil de testear, razonar y optimizar (alto riesgo de regresión).  
   - **Sugerencia**: Separar por etapas (parseo, validación, persistencia, reporte), introducir objetos de resultado y tests por etapa.

10. **`comedores/views/comedor.py::get_relaciones_optimizadas` (~533 líneas)**  
   - **Problema**: Mezcla query-building, reglas de negocio y composición de contexto.  
   - **Impacto**: Baja cohesión y alto acoplamiento con vista.  
   - **Sugerencia**: Mover a servicio/repositorio de consultas + funciones puras pequeñas.

11. **`celiaquia/views/validacion_renaper.py::_consultar_renaper` (~360 líneas)**  
   - **Problema**: Flujo extenso con I/O externo y lógica de control.  
   - **Impacto**: Difícil de mockear y recuperar errores de red de forma consistente.  
   - **Sugerencia**: Encapsular cliente RENAPER, normalizar errores y agregar retries/backoff explícitos.

12. **`relevamientos/serializer.py::clean` (~223 líneas)**  
   - **Problema**: Validación de muchos campos en un único método.  
   - **Impacto**: Alto costo cognitivo; edge cases más fáciles de romper.  
   - **Sugerencia**: Dividir en validadores por dominio (`clean_*`) y utilidades reutilizables.

### 4) Módulos de baja cohesión / “god files”

13. **`admisiones/services/admisiones_service.py` (1727 líneas), `admisiones/views/web_views.py` (1398), `relevamientos/service.py` (1205), `comedores/services/comedor_service.py` (1191)**  
   - **Problema**: Módulos extremadamente grandes con múltiples responsabilidades.  
   - **Impacto**: Onboarding lento, mayor deuda técnica, testing difícil y regresiones frecuentes.  
   - **Sugerencia**: Refactor incremental por casos de uso (sin breaking changes), añadiendo tests de caracterización antes de extraer.

### 5) Config/scripts desactualizados o innecesarios

14. **`package.json`**  
   - **Problema**: `scripts.test` está hardcodeado para fallar (`echo "Error: no test specified" && exit 1`) y `dependencies` vacío, pese a existir tests JS.  
   - **Impacto**: Pipeline Node inusable y señal confusa para nuevos devs.  
   - **Sugerencia**: Definir runner real (`node --test` o `jest`) o eliminar `package.json` si no se usa Node como toolchain.

15. **`docker/django/entrypoint.py`**  
   - **Problema**: Ejecuta `makemigrations` en cada arranque.  
   - **Impacto**: Riesgo operativo (migraciones accidentales en runtime), tiempos de arranque y no determinismo entre entornos.  
   - **Sugerencia**: Mover `makemigrations` fuera del entrypoint (flujo de desarrollo/CI), dejar solo `migrate --noinput`.

16. **`README.md`**  
   - **Problema**: Referencias a repo/ruta histórica `SISOC` (`git clone .../SISOC.git`, `cd SISOC`) que no coincide con el nombre real actual.  
   - **Impacto**: Setup inicial confuso para nuevos integrantes.  
   - **Sugerencia**: Actualizar comandos de onboarding al nombre/repositorio vigente.

### 6) Inconsistencias de naming/formato/convenios

17. **`tests/test_clasificacion/test_clasifiacion_comedor_service_puntuacion_0.py` y `_56.py`**  
   - **Problema**: “clasifiacion” está mal escrito (debería “clasificacion”).  
   - **Impacto**: Búsqueda más difícil y menor consistencia de naming.  
   - **Sugerencia**: Renombrar archivos y actualizar imports/rutas de test.

18. **`rendicioncuentasmensual/models.py`**  
   - **Problema**: `related_name="arvhios_adjuntos"` con typo y `FIXME` explícito.  
   - **Impacto**: API ORM inconsistente; potencial deuda permanente si terceros ya dependen del typo.  
   - **Sugerencia**: Plan de deprecación: agregar alias temporal, migración de callers y luego corrección definitiva.

### 7) Tests faltantes o frágiles

19. **`tests/escape_html.test.js`**  
   - **Problema**: Script “manual test” que no está integrado al runner ni falla automáticamente.  
   - **Impacto**: Cobertura no verificable en CI.  
   - **Sugerencia**: Convertir a test automatizado ejecutado por npm script o eliminarlo.

20. **Cobertura de regresión limitada para módulos más complejos** (`admisiones/services/admisiones_service.py`, `relevamientos/service.py`, `celiaquia/services/importacion_service.py`)  
   - **Problema**: Alta complejidad/cantidad de lógica frente a cobertura no proporcional.  
   - **Impacto**: Alto riesgo de regresión silenciosa.  
   - **Sugerencia**: Priorizar tests de caracterización y rutas críticas (errores de integración, edge cases y autorización).

### 8) TODO/FIXME y hotspots de deuda técnica

21. **`relevamientos/service.py`**, **`relevamientos/serializer.py`**, **`relevamientos/tasks.py`**, **`config/middlewares/csp.py`**, **`templates/includes/base.html`**, **`templates/includes/new_base.html`**  
   - **Problema**: Concentración de TODO/FIXME en flujo crítico (relevamientos y seguridad frontend/CSP).  
   - **Impacto**: Señales de fragilidad y deuda acumulada.  
   - **Sugerencia**: Crear backlog técnico priorizado por riesgo (seguridad > estabilidad > limpieza).

### 9) Dependency bloat / higiene de dependencias

22. **`requirements.txt`**  
   - **Problema**: Mezcla dependencias runtime, tooling y test en un único archivo grande.  
   - **Impacto**: Entornos más pesados/lentos y mayor superficie de CVEs.  
   - **Sugerencia**: Separar en `requirements/base.txt`, `dev.txt`, `test.txt` y revisar paquetes no usados en import directo.

23. **`package-lock.json` + `package.json` sin dependencias**  
   - **Problema**: Artefactos Node presentes sin stack JS formalmente definida.  
   - **Impacto**: Ruido de mantenimiento.  
   - **Sugerencia**: O formalizar toolchain JS o remover lockfile/package si no aplica.

### 10) Security smells

24. **`config/middlewares/csp.py`**  
   - **Problema**: CSP permite `'unsafe-inline'` y `'unsafe-eval'` (además marcado como TODO).  
   - **Impacto**: Mayor exposición a XSS/ejecución de script inyectado.  
   - **Sugerencia**: Migrar a nonces/hashes y eliminar gradualmente directivas inseguras.

25. **`admisiones/templates/admisiones/admisiones_tecnicos_form.html` y `celiaquia/templates/celiaquia/expediente_list.html`**  
   - **Problema**: Inyección de `window.CSRF_TOKEN` en `<script>` inline.  
   - **Impacto**: Dificulta endurecer CSP y fomenta inline scripts.  
   - **Sugerencia**: Pasar token por meta tag/data-attributes y scripts externos con nonce.

26. **`docker/django/entrypoint.py`**  
   - **Problema**: `subprocess.run(...)` sin `check=True`; fallos de comandos pueden continuar silenciosamente.  
   - **Impacto**: Arranques “exitosos” con estado inconsistente.  
   - **Sugerencia**: Activar `check=True` y manejo de errores explícito por etapa.

---

## Priorización sugerida (alto impacto primero)
1. Seguridad frontend/CSP (`unsafe-inline` / `unsafe-eval`) + scripts inline.
2. Estabilidad operativa del entrypoint (`makemigrations` runtime y `subprocess` sin `check`).
3. Limpieza de tests muertos/duplicados en `tests/test_clasificacion/`.
4. Refactor incremental de funciones >200 líneas y módulos de baja cohesión.
5. Higiene de dependencias/config (requirements por entorno + package.json coherente).
