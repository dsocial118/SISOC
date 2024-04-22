# Historia Social Única
Mati
## ACERCA DEL PROYECTO:

App web que permite visualizar y gestionar información de personas en situación de vulnerabilidad, sus dimensiones (familia, vivienda, economía, trabajo, salud, etc.) y realizar un seguimiento de los objetivos e intervenciones realizadas desde los organismos que trabajan acompañandolas.  


---
## TECNOLOGÍAS UTILIZADAS

![HTML5](https://img.shields.io/badge/-HTML5-%23F11423?style=flat-square&logo=html5&logoColor=ffffff)
![CSS3](https://img.shields.io/badge/-CSS3-%231572B6?style=flat-square&logo=css3)
![JavaScript](https://img.shields.io/badge/-JavaScript-%23F7DF1C?style=flat-square&logo=javascript&logoColor=000000&labelColor=%23F7DF1C&color=%23FFCE5A)
![Bootstrap](https://img.shields.io/badge/-Bootstrap-BE85C6?style=flat-square&logo=Bootstrap)
![Python](http://img.shields.io/badge/-Python-DAD031?style=flat-square&logo=python)
![Django](http://img.shields.io/badge/-Django-025922?style=flat-square&logo=django&logoColor=025922&labelColor=DAD031)
![MySQL](https://img.shields.io/badge/-MySQL-ffffff?style=flat-square&logo=mysql)
![Github](https://img.shields.io/badge/Github-000?style=flat-square&logo=Github)



---

## REQUISITOS

> python 3.7 o superior

> Mysql 5.0 o superior (Solo para el uso en Ambiente de Producción)

> Paquetes y librerías: Se encuentran en el archivo requirements.txt y deben instalarse mediante el comando:

```
    pip install -r requirements.txt
```
    
##### Actulamente:
- Django==4.0.2
<small> Ver documentacion en https://docs.djangoproject.com/en/4.2/releases/4.0.2/</small>
- crispy-bootstrap4==2022.1
<sub> Ver documentacion en https://pypi.org/project/crispy-bootstrap4/</sub>
- django-extensions==3.2.1
<sub> Ver documentacion en https://django-extensions.readthedocs.io/en/latest/installation_instructions.html</sub>
- docutils==0.19
<sub> Ver documentacion en https://pypi.org/project/docutils/</sub>
- mysqlclient==2.1.1
<sub> Ver documentacion en https://pypi.org/project/mysqlclient/</sub>
- Pillow==9.4.0
<sub> Ver documentacion en https://pypi.org/project/Pillow/</sub>

---

## DESPLIEGUE
1. Cambiar el direccionamiento de la Base de Datos en el archivo .config/settings.py  ( <sub> [Ver documentación](https://docs.djangoproject.com/en/4.0/ref/settings/#databases) </sub> ) y correr las migraciones:
    ```
        python manage.py makemigrations 
        python manage.py migrate 
    ```
   
2. Debe cambiarse en el archivo .config/settings.py las opciones:
     ```
        DEBUG = False 
        ALLOWED_HOSTS = ['*']  #<---- colocar el host
     ```

3. Debe correr un colector de statics, el cual crea la carpeta STATIC_ROOT para alojar todos los static:
 
    <sub> Ver documentacion [aqui](https://docs.djangoproject.com/en/4.0/howto/static-files) </sub>
    ```
        python manage.py collectstatic
    ```

---

## ESTRUCTURA DE LAS APPS PROYECTO DJANGO


<img src="https://github.com/mariana-git/HSU/assets/88113403/e16e2cd2-9840-44b7-a736-9492e888da4d" width="400" />

---

<center><sub>Desarrolladores:  Mariana Sayago - Pablo Cao</sub></center>

