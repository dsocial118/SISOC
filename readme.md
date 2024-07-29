# SISOC

App web que permite visualizar y gestionar información de personas en situación de vulnerabilidad, sus dimensiones (familia, vivienda, economía, trabajo, salud, etc.) y realizar un seguimiento de los objetivos e intervenciones realizadas desde los organismos que trabajan acompañandolas.  

## Despliegue local

1. Clonar el repositorio e ingresar en el
2. Solicitar al DevOps un dump de la DB y colocarlo en `./docker/mysql/local-dump.sql` para que se cargue en el MySQL **(opcional)**
3. Ejecutar `docker-compose up` y esperar a que los servicios se levanten (si se aplico un dump, va a tardar unos minutos)
4. Crear un super usuario para ingresar a SISOC ejecutando `docker-compose exec django python manage.py createsuperuser` **(opcional)**

### Levantar nueva DB a MySQL (Cuando el servicio de MySQL ya fue levantado pero se quiere cambiar la DB)
1. Detener los serviicos con `docker-compose down`
2. Borrar volumen de la DB ejecutando `docker volume rm sisoc_mysql_data`
3. Colocar dump en `./docker/mysql/local-dump.sql`
4. Correr nuevamente `docker-compose up`

### Debug en docker-compose
1. Ejecutar nuestra app con `docker-compose up` y esperar al output: `Starting development server at http://0.0.0.0:8000/`
2. En la pestaña del debugger de VSCode, seleccionar la opcoin `Djangp in Docker` e iniciar debugging
3. Utilizarlo como cualquier otro debugger, recordando que depende del proceso principal de docker-compose

## API

TODO: Agregar documentacion para la API

## Variables de entorno

```
DEBUG=boolean
DJANGO_SECRET_KEY=string
DJANGO_ALLOWED_HOSTS=string with hosts separated by spaces
SQL_HOST=string
SQL_USER=string
SQL_PASSWORD=string
SQL_NAME=string
```

## TECNOLOGÍAS UTILIZADAS

![HTML5](https://img.shields.io/badge/-HTML5-%23F11423?style=flat-square&logo=html5&logoColor=ffffff)
![CSS3](https://img.shields.io/badge/-CSS3-%231572B6?style=flat-square&logo=css3)
![JavaScript](https://img.shields.io/badge/-JavaScript-%23F7DF1C?style=flat-square&logo=javascript&logoColor=000000&labelColor=%23F7DF1C&color=%23FFCE5A)
![Bootstrap](https://img.shields.io/badge/-Bootstrap-BE85C6?style=flat-square&logo=Bootstrap)
![Python](http://img.shields.io/badge/-Python-DAD031?style=flat-square&logo=python)
![Django](http://img.shields.io/badge/-Django-025922?style=flat-square&logo=django&logoColor=025922&labelColor=DAD031)
![MySQL](https://img.shields.io/badge/-MySQL-ffffff?style=flat-square&logo=mysql)
![Github](https://img.shields.io/badge/Github-000?style=flat-square&logo=Github)