# Alineación mínima de drift de dependencias y SDK

## Contexto

Se detectaron dos desalineaciones concretas en el repo:

- `requirements/base.txt` fija `PyMySQL==1.1.1`, pero `docker/django/Dockerfile` reinstalaba `pymysql` sin versión.
- `requirements/dev.txt` fija `pylint==3.2.6`, pero `.github/workflows/lint.yml` instalaba `pylint` sin versión en el job `setup`.

## Cambio realizado

- Se eliminó la instalación flotante de `pymysql` en la imagen Docker de Django para dejar `requirements/*.txt` como fuente de verdad.
- Se alineó la instalación de `pylint` en CI con la versión pinneada en `requirements/dev.txt`.

## Impacto

- Reduce drift entre build local, contenedor y CI.
- Evita que una resolución de `pip` posterior introduzca una versión distinta a la declarada en el repo.
- No cambia comportamiento funcional de la aplicación.
