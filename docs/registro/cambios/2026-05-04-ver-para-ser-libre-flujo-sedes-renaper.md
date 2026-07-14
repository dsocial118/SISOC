# Ver Para Ser Libres: sedes, registros y RENAPER

## Contexto

Se amplio el modulo Ver Para Ser Libres para reducir friccion operativa en la carga de itinerarios, jornadas y registros nominales.

## Cambios

- El autocomplete de sedes en nuevo itinerario filtra por la provincia seleccionada y busca por nombre, CUE, domicilio, localidad y jurisdiccion.
- La jornada muestra mapa de sede y resumen de provincia, localidad y calle/altura.
- El registro nominal permite guardar y continuar cargando nuevos registros en la misma jornada, heredando fecha de atencion y sede desde la jornada.
- Se agregaron flags de validacion RENAPER y no verificacion para registros nominales.
- Se agregaron DNI, sexo y estado de validacion RENAPER para referente de jornada.
- Se agrego el modulo Sedes VPSL con grilla, busqueda, alta, edicion, checklist, mapa y eliminacion logica.
- La creacion de jornadas bloquea fechas ya utilizadas dentro del mismo itinerario antes de guardar, evitando errores de unicidad de base de datos.

## Decision

Se reutiliza la consulta RENAPER ya expuesta por `ComedorService.obtener_datos_ciudadano_desde_renaper` para evitar duplicar integracion externa. Las sedes pasan a usar `SoftDeleteModelMixin`, consistente con el patron de borrado logico del proyecto.

## Validacion esperada

- Tests puntuales del modulo `ver_para_ser_libre`.
- `makemigrations --check --dry-run` dentro de Docker.
