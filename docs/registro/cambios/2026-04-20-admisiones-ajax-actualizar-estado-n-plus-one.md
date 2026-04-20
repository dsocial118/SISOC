# Admisiones: refactor para evitar N+1 en ajax/actualizar-estado

Fecha: 2026-04-20

## Contexto

En el flujo `admisiones/ajax/actualizar-estado/`, al cambiar el estado de un
`ArchivoAdmision`, el service disparaba validaciones sobre documentacion
obligatoria de la admision.

La causa raiz del problema de performance estaba en
`AdmisionService._todos_obligatorios_aceptados()` y
`AdmisionService._todos_obligatorios_tienen_archivos()`: ambos iteraban los
documentos obligatorios y, por cada documento, ejecutaban
`ArchivoAdmision.objects.filter(...).first()`.

Ese patron generaba un N+1:

- 1 query para obtener `Documentacion` obligatoria.
- N queries adicionales para buscar el `ArchivoAdmision` de cada documento.

En Django Debug Toolbar esto se manifestaba como multiples queries casi
identicas sobre `admisiones_archivoadmision`, cambiando solo
`admision_id`/`documentacion_id`.

## Cambio aplicado

- Se refactorizo `_iter_documentos_obligatorios_admision()` para usar
  `prefetch_related(Prefetch(...))` y cargar en bloque los `ArchivoAdmision`
  relevantes para la admision.
- Se extrajo `_obtener_archivo_obligatorio_admision(...)` para resolver el
  archivo desde el prefetch cuando esta disponible y conservar un fallback
  seguro cuando no lo esta.
- `actualizar_estado_ajax()` ahora obtiene el `ArchivoAdmision` puntual con
  `select_related("admision", "documentacion")`, evitando queries accesorias
  cuando luego se accede a esas relaciones.

## Decision clave

Para este caso, la mejor correccion no era solo agregar `select_related()` al
objeto puntual, porque el N+1 principal no venia de navegar una FK perezosa,
sino de ejecutar queries manuales dentro de un loop.

La decision fue combinar:

- `prefetch_related()` para eliminar el N+1 estructural del chequeo de
  obligatorios;
- `select_related()` para el `ArchivoAdmision` individual cargado por el
  endpoint, donde si aporta una mejora local clara.

## Validacion

- Verificacion funcional manual del flujo `/ajax/actualizar-estado/`.
- Observacion en Django Debug Toolbar: la familia de queries sobre
  `admisiones_archivoadmision` dejo de repetirse N veces en el mismo request.
- Test ejecutado dentro de Docker:

```bash
docker compose exec django pytest tests/test_admisiones_service_helpers_unit.py -q
```

Resultado:

```text
26 passed in 3.78s
```

## Nota para futuros desarrollos

Si un flujo itera objetos y dentro del loop hace `Model.objects.filter(...).first()`,
hay alta probabilidad de introducir un N+1. En esos casos conviene priorizar:

- `select_related()` para FK/OneToOne cuando el acceso es desde el hijo al padre;
- `prefetch_related()` para reverse FK/M2M cuando el acceso es desde el padre a
  muchos hijos;
- carga en bloque y resolucion en memoria cuando el problema nace de queries
  manuales dentro de loops.
