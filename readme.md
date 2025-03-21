# SISOC

## Despliegue local

1. Clonar el repositorio e ingresar en el
2. Solicitar al DevOps un dump de la DB y colocarlo en `./docker/mysql/local-dump.sql` para que se cargue en el MySQL **(opcional)**
3. Ejecutar `docker-compose up` y esperar a que los servicios se levanten (si se aplico un dump, va a tardar unos minutos)
4. Utilizar el usuario predeterminado. Username: 1. Password: 1 **(opcional)**

## Formateo y parseo de codigo previo al pull request
### PyLint (se debe arreglar el codigo manualmente):
`pylint **/*.py --rcfile=.pylintrc`
### Black (automatico):
`black .`
### DJlint (automatico en la mayoria de los casos):
`djlint . --configuration=.djlintrc --reformat`

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

# Ejecutar tests automaticos
`docker compose exec django pytest -n auto`

# Buenas practicas a seguir
1. Utilizar SNAKE CASE en todo el codigo Python. Utilizar CamelCase en todo el codigo JavaScript.
2. Respetar el modelo "Modelo - Template - Vista" que propone Django.
    - Modelo: Representa a la tabla de la DB. Cada clase debe tener su docstring para saber que hace cada campo. Cada campo debe tener su verbose_name si se va a usar en un formulario. Los campos deben ser los justos y necesarios, evitar redundancia. De aca salen las migraciones, revisar las que mandan a git. El nombre de los modelos debe ser en singular. Cada modelo debe ser registrado en el admin.
    - Vista: Responsable de manejar las peticiones HTTP, interactuar con la logica de negocio (Dentro de servicios, no de la vista) y devolver una respuesta. Siempre usar vistas basadas en clase (para aprovechar las vistas genericas de Django como ListView). Manejar correctamente las excepciones con mensajes de error
    - Template: El HTML de la presentacion. Evitar importaciones innecesarias. Mantener archivos pequeños aprovechando la herencia de plantillas. Evitar consultas en plantillas. Separar el CSS y el JS del HTML. 
3. Mantener el orden en los archivos. Por ejemplo: Dentro de la aplicacion "comedores", dentro de la carpeta "templates", se deben separar los .html del modelo "Relevamiento" de los del modelo "Observacion". Lo mismo para la logica de negocio del modelo "Comedor", que se encuentra en la carpeta "services" dentro de la clase "ComedorService"
4. Antes de pushear el codigo y hacer el pull request (o cuando los actions de github mencionen algun error), se deben ejecutar los comandos para formatear y parsear el codigo (mencionados en el readme.md)

## TECNOLOGÍAS UTILIZADAS

![HTML5](https://img.shields.io/badge/-HTML5-%23F11423?style=flat-square&logo=html5&logoColor=ffffff)
![CSS3](https://img.shields.io/badge/-CSS3-%231572B6?style=flat-square&logo=css3)
![JavaScript](https://img.shields.io/badge/-JavaScript-%23F7DF1C?style=flat-square&logo=javascript&logoColor=000000&labelColor=%23F7DF1C&color=%23FFCE5A)
![Bootstrap](https://img.shields.io/badge/-Bootstrap-BE85C6?style=flat-square&logo=Bootstrap)
![Python](http://img.shields.io/badge/-Python-DAD031?style=flat-square&logo=python)
![Django](http://img.shields.io/badge/-Django-025922?style=flat-square&logo=django&logoColor=025922&labelColor=DAD031)
![MySQL](https://img.shields.io/badge/-MySQL-ffffff?style=flat-square&logo=mysql)
![Github](https://img.shields.io/badge/Github-000?style=flat-square&logo=Github)
