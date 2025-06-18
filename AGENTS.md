# Recomendaciones para la IA

Este archivo resume sugerencias para que un asistente automatico pueda comprender y trabajar en este repositorio. Tambien sirve como guia para desarrolladores que quieran mejorar la documentacion y los scripts de setup.

## Comandos principales
- `docker-compose up` levanta los servicios definidos en `docker-compose.yml`. Utilizarlo para iniciar la aplicacion en modo local.
- `docker compose exec django pytest -n auto` ejecuta los tests automaticos.
- `black .`, `pylint **/*.py --rcfile=.pylintrc` y `djlint . --configuration=.djlintrc --reformat` formatean el codigo y las plantillas.

## Sugerencias de codigo
- Incluir docstrings descriptivas en vistas, modelos y servicios para que quede clara su responsabilidad.
- Mantener el orden de las carpetas siguiendo la estructura actual: cada modulo dentro de su app correspondiente.
- Escribir pruebas para la logica de negocio en `tests/` y mantenerlas actualizadas.

## Setup del entorno
- Copiar el archivo `.env.example` y renombrarlo a `.env` para definir las variables de entorno necesarias. Los nombres estan detallados en la seccion "Variables de entorno" del `readme.md`.
- Incluir ejemplos o scripts de carga de datos en `docker/mysql` para acelerar el despliegue local.

Estas practicas facilitaran la comprension del sistema tanto para humanos como para herramientas de analisis automatico.
