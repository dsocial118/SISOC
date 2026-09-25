# REQ — Permitir sedes adicionales en cualquier departamento de la provincia

| | |
|---|---|
| **Tipo** | Corrección funcional (bloqueante operativo) |
| **Sistema / Módulo** | SISOC — INET/VAT, legajo del Centro → Ubicaciones adicionales |
| **Estado** | Implementado |

## Situación actual

En el legajo del Centro, solapa **Ubicaciones adicionales** → botón *Agregar
sede*, el desplegable **Localidad** solo ofrece las localidades del mismo
departamento (municipio) que el centro.

El filtro está en `build_localidad_queryset_for_centro()`
(`VAT/forms.py:205-213`): si el centro tiene municipio y ese municipio tiene
localidades, devuelve **solo** esas. Recién si el municipio no tiene ninguna cae
a las de la provincia.

```python
if centro.municipio_id:
    municipio_queryset = queryset.filter(municipio_id=centro.municipio_id)
    if municipio_queryset.exists():
        return municipio_queryset   # ← acá se corta
```

Hay CFP con sedes en otros municipios que **no pueden cargarlas**, por lo que
quedan mal registradas o directamente sin registrar.

## Objetivo

Que al agregar una sede se pueda elegir cualquier departamento y localidad **de
la provincia del centro**, sin quedar atado al departamento del centro.

## Alcance

Territorialmente, el alcance es **provincial**: se habilitan todos los
departamentos y localidades de la provincia del centro. No se amplía a otras
provincias, porque la operación de los CFP ya es provincial y mantener ese
límite evita cargas erróneas fuera de jurisdicción.

| Capa | A modificar |
|---|---|
| `VAT/forms.py:205` | `build_localidad_queryset_for_centro()`, origen de la restricción |
| `VAT/views/centro.py:201` | Asigna ese queryset al form del modal *Agregar sede* |
| `VAT/views/institucion.py:381` | Endpoint AJAX de localidades por centro, usa el mismo builder |
| Modal *Agregar Ubicación* | Incorporar el selector de departamento y su cascada |

**No incluye** cambios en la base: `InstitucionUbicacion` guarda únicamente
`localidad`, así que el selector de departamento es solo una ayuda de filtrado
en pantalla. No hace falta migración.

## Requerimiento funcional

1. El desplegable de localidad deja de limitarse al departamento del centro y
   pasa a ofrecer las de toda la provincia del centro. En la práctica, alcanza
   con eliminar el atajo por municipio y dejar el filtro por provincia que la
   función ya tiene.
2. Agregar un selector **Departamento** con todos los de la provincia del
   centro. **Localidad** arranca vacía y se completa por AJAX recién al elegir
   un departamento, con el endpoint existente `ajax_load_localidades`
   (`core/urls.py`). Así el HTML no trae las miles de localidades de una
   provincia grande en cada carga del legajo.
3. El servidor sigue validando la localidad contra toda la provincia: solo
   cambia lo que se renderiza, no lo que se acepta. En edición, el
   departamento arranca preseleccionado en el de la localidad guardada.
4. Las sedes ya cargadas siguen viéndose y editándose igual.

El alcance territorial por usuario no requiere tratamiento adicional: los
usuarios ya operan limitados a su provincia, que es el mismo límite que impone
este cambio.

## Criterios de aceptación

- [ ] Se puede crear una sede adicional en un departamento distinto al del
      centro, dentro de la misma provincia.
- [ ] El selector de localidad se filtra según el departamento elegido.
- [ ] No se ofrecen departamentos ni localidades de otras provincias.
- [ ] Las sedes existentes se listan y editan sin cambios.
- [ ] El endpoint de localidades por centro sigue respondiendo correctamente.

## Riesgos

- El mismo builder alimenta el endpoint de `institucion.py:381`. Hay que revisar
  qué consume ese endpoint antes de ampliarlo, para no cambiar sin querer el
  comportamiento de otra pantalla.
- Centros sin provincia cargada: hoy la función cae a devolver todas las
  localidades del país. Conviene verificar si existen esos casos y definir el
  comportamiento esperado.
