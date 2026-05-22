# Fix de resolucion de dependencias de runtime

## Contexto

El build de la imagen `docker/django/Dockerfile` fallo durante `pip install -r requirements.txt`
porque `requirements/base.txt` tenia dos upgrades parciales de dependencias:

- `cryptography==46.0.5`
- `cffi==1.17.0`
- `weasyprint==68.0`
- `tinycss2==1.4.0`

Desde `cryptography 46.0.5`, el paquete requiere `cffi>=2.0.0` en CPython 3.9+.
Ademas, `weasyprint 68.0` requiere `tinycss2>=1.5.0`.

## Cambio aplicado

- Se actualizo `cffi` de `1.17.0` a `2.0.0` en `requirements/base.txt`.
- Se actualizo `tinycss2` de `1.4.0` a `1.5.0` en `requirements/base.txt`.
- No se modificaron otras dependencias ni el Dockerfile.

## Decision

Se eligio el cambio minimo compatible con los upgrades ya presentes de `cryptography` y
`weasyprint`, para restaurar la resolucion de `pip` sin introducir un refresh mas amplio
del stack.

## Validacion

Se reprodujeron los conflictos en `python:3.11.9-bullseye` con:

```bash
python -m pip install --dry-run -r requirements.txt
```

Luego del cambio, el build de `docker/django/Dockerfile` avanzo con el set de dependencias
alineado usando la misma imagen base.
