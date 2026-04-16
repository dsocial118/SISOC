# SISOC

Sistema de gestión basado en **Django** y **MySQL**, desplegable mediante **Docker** y **Docker Compose**.  
Cada aplicación del repositorio representa un módulo funcional (ej. `comedores`, `relevamientos`, `users`).

> Documentación organizada: ver `docs/indice.md` para el índice y referencias detalladas.
> Setup y operación: `docs/operacion/instalacion.md`, `docs/operacion/infraestructura.md` y `docs/operacion/comandos_administracion.md`.

---

## Tabla de Contenidos

1. [Arquitectura General](#arquitectura-general)  
2. [Requisitos Previos](#requisitos-previos)  
3. [Despliegue Local](#despliegue-local)  
4. [Estructura de Carpetas](#estructura-de-carpetas)  
5. [Formateo y Estilo de Código](#formateo-y-estilo-de-código)  
6. [Variables de Entorno](#variables-de-entorno)  
7. [Tests Automáticos](#tests-automáticos)  
8. [Buenas Prácticas](#buenas-prácticas)  
9. [API](#api)  
10. [Tecnologías Utilizadas](#tecnologías-utilizadas)  
11. [Despliegues](#despliegues)  
12. [Changelog](#changelog)  
13. [Contribución](#contribución)

---

## Arquitectura General

- **Backend**: Django  
- **Base de datos**: MySQL  
- **Contenedores**: Docker + Docker Compose  
- **Front-end**: HTML, CSS, JS, Bootstrap  
- **Tests**: pytest  

---

## Requisitos Previos

- [Docker](https://www.docker.com/) y [Docker Compose](https://docs.docker.com/compose/) instalados.  
- Python 3.11+ (solo si se ejecuta fuera de contenedores).  
- VSCode recomendado con extensión **Python** y **Docker**.  

---

## Despliegue Local

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/dsocial118/SISOC.git
   cd SISOC
   ```
2. (Opcional) Colocar un dump en `./docker/mysql/local-dump.sql`.  
3. Levantar servicios:
   ```bash
   docker compose up
   ```
4. Acceder a la app en [http://localhost:8001](http://localhost:8001) (valor por defecto de `DOCKER_DJANGO_PORT_FORWARD` en `.env.example`).

`docker-compose.yml` queda reservado para desarrollo/local y es el único compose versionado que levanta `mysql`.

## Reiniciar base de datos con nuevo dump
```bash
docker compose down
docker volume rm sisoc_mysql_data
# colocar nuevo dump en ./docker/mysql/local-dump.sql
docker compose up
```

## Debug con VSCode
- Iniciar servicios con `docker compose up`.
- Seleccionar la configuración `Django in Docker` en el panel de debugging.  

---

## Estructura de Carpetas

- **`config/`** → configuración global de Django  
- **`docker/`** → archivos de contenedores  
- **`apps/`** (`comedores/`, `relevamientos/`, `users/`, …) → aplicaciones Django  
- **`templates/`** y **`**/templates/`** → plantillas HTML  
- **`templates/components`** → Componentes HTML  
- **`static/`** → archivos estáticos (CSS, JS, imágenes)  
- **`**/tests/`** → pruebas automáticas  

---

## Formateo y Estilo de Código

Antes de un **Pull Request**, ejecutar:

```bash
# Linter (Se debe resolver a mano)
pylint **/*.py --rcfile=.pylintrc

# Formateo Python (Automagico)
black .

# Formateo Django Templates (Aveces automagico, a veces no)
djlint . --configuration=.djlintrc --reformat
```

---

## Variables de Entorno

Ejemplo y defaults en `.env.example`.
Para más detalle operativo: `docs/operacion/instalacion.md`.

---

## Tests Automáticos

Ejecutar:
```bash
docker compose exec django pytest -n auto
```

Referencia CI actual:
- `tests.yml` corre `smoke`, `migrations_check` y, en PRs, `pytest` con cobertura + `mysql_compat`.
- `lint.yml` corre `encoding_check`, `black`, `djlint` y `pylint`.

---

## Buenas Prácticas

1. **Estilo de código**  
   - Python → `snake_case`  
   - JavaScript → `CamelCase`  

2. **Arquitectura Django**  
   - **Modelo**: docstring + `verbose_name` → evitar redundancia.  
   - **Vista**: usar **Class Based Views**, sin lógica de negocio.  
   - **Template**: evitar consultas y mantener simple.  

3. **Organización interna**  
   - Archivos ordenados por módulo.  
   - Servicios en `services/` por modelo.  
   - Templates separados por entidad.  

4. **Commits**  
   Usar formato consistente:  
   ```
   feat(comedores): nueva funcionalidad
   fix(relevamientos): corregir bug
   refactor(users): limpiar servicios
   ```

   Los cambios importantes deben registrar su contexto en `docs/registro/`.

---

## API

Documentación Postman:  
[API SISOC](https://documenter.getpostman.com/view/14921866/2sAXxMfDXf#01ac9db5-a6b5-4b20-9e8c-973e38884f17)
No es la mejor documentacion. En caso de dudas, consultar con Juani (Tech lead de SISOC) o Andy (Dueño de GESCOM)

Además, el repo expone schema OpenAPI en `/api/schema/`, Swagger en `/api/docs/` y Redoc en `/api/redoc/`.
Ejemplo de request:
```bash
curl -X GET http://localhost:8001/api/comedores/ \
  -H "Authorization: Api-Key <API_KEY>"
```

---

## Despliegues

##Ciclo quincenal de releases
- **Semana 0 (jueves)** → abrir branch `development`.  
- **Semana 2 (lunes, freeze)** → congelar `development`, crear tag `YY.MM.DD-rc1`.  
- **Semana 2 (miércoles noche)** → deploy a PRD si QA aprueba último `rcX`.  

Para detalle operativo vigente de entornos, compose y release, usar `docs/operacion/infraestructura.md`.

##Checklist
- [ ] Branch `development` congelada sin features nuevos  
- [ ] Backup válido de DB  
- [ ] Tag final creado en `development`  
- [ ] Probado con base similar a PRD  
- [ ] Testeado en QA ese mismo tag  
- [ ] QA aprobó el tag  
- [ ] Merge limpio a `main`  
- [ ] Changelog actualizado  
- [ ] Migraciones reversibles/controladas  
- [ ] Equipo notificado  
- [ ] Último tag estable guardado para rollback  
- [ ] Squash de migraciones estables  

---

## Changelog

`CHANGELOG.md`

Los usuarios del sistema pueden consultar las novedades desde la opción **"Novedades del sistema"** en el menú lateral del backoffice.

---

## Contribución

1. Crear una branch desde `development`.  
2. Commit siguiendo el estándar definido.  
3. Abrir **Pull Request** a `development`.  
4. Pasar linters y tests antes del PR.  
5. Revisión de al menos otro dev antes del merge.  

---
