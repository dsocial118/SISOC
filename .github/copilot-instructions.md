# Instrucciones para Agentes de IA - SISOC

Sistema de gestión social (SISOC) basado en Django 4.2, MySQL 8.0 y Docker. Backoffice para gestión de comedores comunitarios, admisiones, acompañamientos y rendiciones de cuenta.

## Arquitectura

### Estructura modular por dominio
- Cada app Django representa un módulo funcional independiente (`comedores/`, `admisiones/`, `centrodefamilia/`, etc.)
- Patrón Service Layer: lógica de negocio separada de vistas en clases Service dentro de `<app>/services/`
- Ejemplo: `comedores/services/comedor_service.py` → clase `ComedorService` con métodos estáticos

### Organización interna de apps
```
<app>/
├── models/          # Modelos de datos (cuando hay múltiples)
├── services/        # Lógica de negocio (clases Service por modelo)
├── forms/           # Formularios Django
├── views/           # Vistas (preferir CBV)
├── templates/       # Templates específicos de la app
├── templatetags/    # Template tags personalizados
└── tests/           # Tests automáticos
```

### Sistema de componentes reutilizables
- Templates reutilizables en `templates/components/` (data_table, search_bar, breadcrumb, modal, etc.)
- Usar `{% include 'components/<nombre>.html' with param=value %}` en lugar de duplicar código
- Ver [templates/components/README_COMPLETE.md](../templates/components/README_COMPLETE.md) para detalles

### Filtros avanzados centralizados
- Sistema `AdvancedFilterEngine` en `core/services/advanced_filters.py`
- Cada app define configuración en `services/<modelo>_filter_config.py`
- Patrón: `FIELD_MAP`, `FIELD_TYPES`, operadores por tipo (`TEXT_OPS`, `NUM_OPS`, `CHOICE_OPS`)

## Convenciones críticas

### Vistas
- **Siempre usar Class-Based Views** (ListView, DetailView, CreateView, UpdateView, DeleteView)
- Heredar `LoginRequiredMixin` para protección de autenticación
- Para FBVs, decorar con `@login_required` o `@group_required(["NombreGrupo"])`
- Sin lógica de negocio en vistas: delegar a Services
- Ejemplo:
```python
class ComedorListView(LoginRequiredMixin, ListView):
    model = Comedor
    template_name = "comedores/comedor_list.html"
    
    def get_queryset(self):
        return ComedorService.get_filtered_queryset(self.request)
```

### Permisos y grupos
- Grupos definidos en `core/constants.py` → clase `UserGroups`
- Usar decorador `@group_required(["Tecnico Comedor", "Coordinador Gestion"])` (ver `core/decorators.py`)
- Superusers siempre tienen acceso completo

### Modelos
- Docstrings descriptivas en modelos y campos complejos
- Usar `verbose_name` y `verbose_name_plural` para UI
- Evitar redundancia entre nombre de campo y `verbose_name`

### Templates
- NO hacer consultas a BD en templates
- Preferir `{% include 'components/...' %}` sobre duplicación
- djlint para formateo: `djlint . --configuration=.djlintrc --reformat`

## Comandos esenciales

### Desarrollo local
```bash
# Levantar servicios
docker-compose up

# Reiniciar BD con nuevo dump
docker-compose down
docker volume rm sisoc_mysql_data
# Colocar dump en ./docker/mysql/local-dump.sql
docker-compose up

# Ejecutar comando en Django
docker compose exec django python manage.py <comando>
```

### Tests
```bash
# Ejecutar todos los tests en paralelo
docker compose exec django pytest -n auto

# Tests específicos
docker compose exec django pytest comedores/tests.py -v
```

### Formateo y linting (REQUERIDO antes de PR)
```bash
# Python - autoformato
black .

# Python - linting (resolver manualmente)
pylint **/*.py --rcfile=.pylintrc

# Django Templates - autoformato
djlint . --configuration=.djlintrc --reformat
```

### Debug
- VSCode: configuración "Django in Docker" disponible
- Breakpoints funcionan en código Django dentro del container

## Patrones específicos del proyecto

### Services con métodos estáticos
```python
class ComedorService:
    """Operaciones de alto nivel relacionadas a comedores."""
    
    @staticmethod
    def get_comedor(pk_send, as_dict=False):
        # Lógica de negocio aquí
```

### Contexto de templates desde services
- Services construyen contexto completo para vistas
- Ejemplo: `AdmisionService.build_list_context(request, queryset)`
- Incluye paginación, breadcrumbs, filtros, columnas personalizables

### Integración RENAPER
- Servicio `centrodefamilia/services/consulta_renaper.py` → `consultar_datos_renaper()`
- Usado en múltiples apps para validación de ciudadanos

### Auditlog automático
- Middleware `auditlog.middleware.AuditlogMiddleware` activo
- Registra cambios automáticamente en modelos registrados

## Variables de entorno críticas
Ver `.env.example` para lista completa. Principales:
- `DJANGO_DEBUG=True/False`
- `ENVIRONMENT=dev|qa|prd`
- `DATABASE_NAME`, `DATABASE_PASSWORD`
- `DJANGO_ALLOWED_HOSTS`, `DJANGO_SECRET_KEY`

## Workflow de desarrollo

### Ciclo quincenal de releases
- Semana 0 (jueves): desarrollo en `development`
- Semana 2 (lunes): freeze + tag `YY.MM.DD-rc1`
- Semana 2 (miércoles): deploy a PRD tras aprobación QA
- Ver checklist completo en sección "Despliegues" del [README.md](../README.md)

### Commits
```
feat: nueva funcionalidad en comedores
fix: corregido bug en relevamientos  
refactor: limpieza en servicios de users
```

### Pull Requests
1. Branch desde `development`
2. Formatear código (black + djlint)
3. Pasar linters (pylint)
4. Tests pasando
5. Revisión de al menos 1 dev

## Tecnologías clave
- **Backend**: Django 4.2.27, Python 3.11.9
- **BD**: MySQL 8.0
- **Frontend**: Bootstrap 5, crispy-forms, templates Django
- **API**: Django REST Framework + drf-spectacular (OpenAPI)
- **Testing**: pytest + pytest-django + pytest-xdist (paralelización)
- **Contenedores**: Docker + Docker Compose

## Referencias rápidas
- Documentación detallada: `docs/indice.md`
- API Postman: [Documentación](https://documenter.getpostman.com/view/14921866/2sAXxMfDXf)
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- Recomendaciones para IA: [AGENTS.md](../AGENTS.md)

## Patrones a EVITAR
❌ Lógica de negocio en vistas  
❌ Consultas a BD en templates  
❌ FBVs sin decorador de autenticación  
❌ Hardcodear nombres de grupos (usar `UserGroups`)  
❌ Duplicar templates (usar componentes)  
❌ Commits sin formatear código
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 69, in __getitem__
     return self._engines[alias]
            ~~~~~~~~~~~~~^^^^^^^
 KeyError: 'django'
 
 During handling of the above exception, another exception occurred:
 
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 128, in get_package_libraries
     module = import_module(entry[1])
              ^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
     return _bootstrap._gcd_import(name[level:], package, level)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
   File "/sisoc/core/templatetags/custom_filters.py", line 6, in <module>
     from django.template.base import Undefined
 ImportError: cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 
 The above exception was the direct cause of the following exception:
 
 Traceback (most recent call last):
   File "/sisoc/manage.py", line 38, in <module>
     main()
   File "/sisoc/manage.py", line 34, in main
     execute_from_command_line(sys.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line
     utility.execute()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 436, in execute
     self.fetch_command(subcommand).run_from_argv(self.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 412, in run_from_argv
     self.execute(*args, **cmd_options)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 453, in execute
     self.check()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 485, in check
     all_issues = checks.run_checks(
                  ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/checks/registry.py", line 88, in run_checks
     new_errors = check(app_configs=app_configs, databases=databases)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/contrib/admin/checks.py", line 78, in check_dependencies
     for engine in engines.all():
                   ^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in all
     return [self[alias] for alias in self]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in <listcomp>
     return [self[alias] for alias in self]
             ~~~~^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 85, in __getitem__
     engine = engine_cls(params)
              ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 24, in __init__
     options["libraries"] = self.get_templatetag_libraries(libraries)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 42, in get_templatetag_libraries
     libraries = get_installed_libraries()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in get_installed_libraries
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in <dictcomp>
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 105, in get_template_tag_modules
     for name in get_package_libraries(pkg):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 130, in get_package_libraries
     raise InvalidTemplateLibrary(
 django.template.library.InvalidTemplateLibrary: Invalid template library specified. ImportError raised when trying to load 'core.templatetags.custom_filters': cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)