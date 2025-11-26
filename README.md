# SISOC

Sistema de gestión basado en **Django** y **MySQL**, desplegable mediante **Docker** y **Docker Compose**.  
Cada aplicación del repositorio representa un módulo funcional (ej. `comedores`, `relevamientos`, `users`).

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
   git clone https://github.com/ORGANIZACION/SISOC.git
   cd SISOC
   ```
2. (Opcional) Colocar un dump en `./docker/mysql/local-dump.sql`.  
3. Levantar servicios:
   ```bash
   docker-compose up
   ```
4. Acceder a la app en [http://localhost:8000](http://localhost:8000).

## Reiniciar base de datos con nuevo dump
```bash
docker-compose down
docker volume rm sisoc_mysql_data
# colocar nuevo dump en ./docker/mysql/local-dump.sql
docker-compose up
```

## Debug con VSCode
- Iniciar servicios con `docker-compose up`.  
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

Ejemplo en [.env.example](https://github.com/dsocial118/BACKOFFICE/blob/development/.env.example):

---

## Tests Automáticos

Ejecutar:
```bash
docker compose exec django pytest -n auto
```

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
   feat: nueva funcionalidad en comedores
   fix: corregido bug en relevamientos
   refactor: limpieza en servicios de users
   ```

---

## API

Documentación Postman:  
[API SISOC](https://documenter.getpostman.com/view/14921866/2sAXxMfDXf#01ac9db5-a6b5-4b20-9e8c-973e38884f17)
No es la mejor documentacion. En caso de dudas, consultar con Juani (Tech lead de SISOC) o Andy (Dueño de GESCOM)

Ejemplo de request:
```bash
curl -X GET http://localhost:8000/api/comedores/      -H "Authorization: Bearer <API_KEY>"
```

---

## Despliegues

##Ciclo quincenal de releases
- **Semana 0 (jueves)** → abrir branch `development`.  
- **Semana 2 (lunes, freeze)** → congelar `development`, crear tag `YY.MM.DD-rc1`.  
- **Semana 2 (miércoles noche)** → deploy a PRD si QA aprueba último `rcX`.  

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

[CHANGELOG.md](https://github.com/dsocial118/BACKOFFICE/blob/development/CHANGELOG.md)

---

## Contribución

1. Crear una branch desde `development`.  
2. Commit siguiendo el estándar definido.  
3. Abrir **Pull Request** a `development`.  
4. Pasar linters y tests antes del PR.  
5. Revisión de al menos otro dev antes del merge.  

---
