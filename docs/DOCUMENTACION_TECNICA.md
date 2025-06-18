# Documentación Técnica de SISOC

Este documento describe las consideraciones técnicas más relevantes para trabajar con el proyecto **SISOC**. La guía está orientada a desarrolladores que deseen levantar el entorno de desarrollo, entender la estructura del código y seguir las buenas prácticas establecidas.

## Tabla de Contenidos

1. [Arquitectura General](#arquitectura-general)
2. [Tecnologías Utilizadas](#tecnologias-utilizadas)
3. [Estructura de Carpetas](#estructura-de-carpetas)
4. [Configuración del Entorno de Desarrollo](#configuracion-del-entorno-de-desarrollo)
5. [Variables de Entorno](#variables-de-entorno)
6. [Estilo de Código](#estilo-de-codigo)
7. [Ejecución de Tests](#ejecucion-de-tests)
8. [Despliegue](#despliegue)

## Arquitectura General

El proyecto está desarrollado con **Django** y sigue la estructura típica de un proyecto web basado en este framework. Utiliza **MySQL** como motor de base de datos y se proveen contenedores de **Docker** para facilitar la puesta en marcha del entorno.

Cada aplicación dentro de la carpeta del repositorio representa un módulo funcional (por ejemplo `comedores`, `relevamientos`, `usuarios`, etc.) con sus modelos, servicios y vistas correspondientes.

## Tecnologías Utilizadas

- Python 3
- Django 4
- MySQL
- Docker / Docker Compose
- Bootstrap y JavaScript para la interfaz

Las dependencias Python están definidas en [`requirements.txt`](../requirements.txt) y pueden instalarse mediante `pip` o utilizando los contenedores provistos.

## Estructura de Carpetas

A continuación se listan las carpetas principales del repositorio:

- **`config/`**: configuración global de Django.
- **`docker/`**: archivos de configuración para los contenedores utilizados en desarrollo.
- **`comedores/`, `relevamientos/`, `users/`, etc.**: aplicaciones de Django que contienen modelos, vistas, formularios y servicios específicos.
- **`templates/`**: plantillas HTML utilizadas por las vistas.
- **`static/`**: archivos estáticos (CSS, JavaScript, imágenes).
- **`tests/`**: pruebas automáticas basadas en `pytest`.
- **`docs/`**: documentación del proyecto.

## Configuración del Entorno de Desarrollo

1. Clonar el repositorio e ingresar en la carpeta del proyecto.
2. (Opcional) Solicitar al equipo de DevOps un volcado de la base de datos y colocarlo en `./docker/mysql/local-dump.sql`.
3. Ejecutar `docker-compose up` para levantar los servicios. La primera vez puede demorar unos minutos, especialmente si se carga un dump de base de datos.
4. Una vez iniciado el contenedor de Django, la aplicación estará disponible en `http://0.0.0.0:8000/`.
5. Se puede utilizar el usuario predeterminado `Username: 1` y `Password: 1` para pruebas locales.

### Herramientas de Formateo

Antes de realizar un pull request se recomienda ejecutar los siguientes comandos:

```bash
pylint **/*.py --rcfile=.pylintrc
black .
djlint . --configuration=.djlintrc --reformat
```

Estas herramientas aseguran un estilo de código consistente y facilitan la revisión.

## Variables de Entorno

El proyecto utiliza las siguientes variables de entorno (ver también el [`readme.md`](../readme.md)):

```text
DJANGO_DEBUG=
DJANGO_SECRET_KEY=
DJANGO_ALLOWED_HOSTS=
DATABASE_HOST=
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_NAME=
GESTIONAR_API_KEY=
GESTIONAR_API_CREAR_RELEVAMIENTO=
GESTIONAR_API_CREAR_COMEDOR=
GESTIONAR_API_CREAR_OBSERVACION=
GESTIONAR_API_CREAR_REFERENTE=
DOMINIO=
```

## Estilo de Código

Las buenas prácticas recomendadas incluyen:

1. Utilizar **snake_case** en Python y **CamelCase** en JavaScript.
2. Seguir el patrón Modelo‑Template‑Vista de Django. La lógica de negocio debe estar en servicios, no en las vistas.
3. Mantener archivos pequeños y organizados, separando plantillas y servicios por módulo.
4. Ejecutar las herramientas de formateo antes de subir cambios al repositorio.

## Ejecución de Tests

Para ejecutar las pruebas automáticas dentro del contenedor Django:

```bash
docker compose exec django pytest -n auto
```

## Despliegue

El archivo `docker-compose.yml` define los servicios necesarios para correr la aplicación de forma local o en ambientes de prueba. Para entornos productivos se recomienda adaptar estas configuraciones según las necesidades de infraestructura (variables de entorno, bases de datos externas, etc.).

---

Con esta guía podrás comprender de manera rápida la estructura y el flujo de trabajo del proyecto **SISOC**. Ante cualquier duda adicional, consulta la documentación del framework Django o contacta al equipo de desarrollo.
