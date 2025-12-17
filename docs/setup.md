# Setup local

## Requisitos
- Docker y Docker Compose instalados; Python 3.11+ solo si se corre fuera de contenedores; VSCode recomendado. Evidencia: README.md:36-40.

## Variables de entorno
- Copiar `.env.example` a `.env` y completar Django, base de datos, puertos y claves de GESTIONAR/RENAPER. Evidencia: .env.example:1-51.

## Despliegue local con Docker Compose
- Colocar opcionalmente un dump en `docker/mysql/local-dump.sql`, luego levantar servicios con `docker-compose up` y acceder en `http://localhost:8000`. Evidencia: README.md:45-64.
- Servicios definidos: contenedor `mysql` y `django`, con volúmenes y puertos parametrizados. Evidencia: docker-compose.yml:1-34.

## Flujo de arranque en el contenedor Django
- Al iniciar, el entrypoint ejecuta `makemigrations`, `migrate`, carga fixtures (`load_fixtures`) y crea usuarios/grupos de prueba (`create_test_users`, `create_groups`); usa Gunicorn en QA/PRD y runserver en DEV. Evidencia: docker/django/entrypoint.py:55-95.

## Debug y desarrollo
- Debug recomendado en VSCode con la configuración “Django in Docker”; levantar servicios antes con `docker-compose up`. Evidencia: README.md:66-68.

## Tests automáticos
- Ejecutar `docker compose exec django pytest -n auto` desde el host. Evidencia: README.md:107-112 y AGENTS.md:5-8.
