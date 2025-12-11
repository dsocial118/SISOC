# Revisión Fix_EliminacionEstados → development

## 0) Resumen de cambios a mergear
- Alcance: **bugfix** en auditoría y flujo de estados de comedores. Tocado: 10 archivos (≈+145/-56 LOC), sin migraciones.
- Áreas: app `audittrail` (views/templates), `comedores` (forms/views), `celiaquia` (servicio importación), `relevamientos` (models), config `.pylintrc`.
- Compatibilidad: sin cambios de API/DB; se excluye `ultimo_estado` del form para evitar sobreescritura.
- Riesgos (top 3):
  1. Resolución de cambios en auditoría dispara consultas por cambio → N+1 en listados. Mitigar con caché/bulk lookup.
  2. Creación/edición de comedor no es atómica: si falla carga de imágenes queda guardado con historial parcial. Mitigar con `transaction.atomic()` y manejo explícito de errores.
  3. Restablecimiento manual de `ultimo_estado` depende de lógica en `save`; falta cobertura de tests. Mitigar con tests de regresión y asserts en form.
- Impacto ops: sin migraciones ni seeds; sin flags. No se tocan settings.
- Rollback: revertir PR/commit y limpiar historiales generados; no hay migraciones que revertir.

## 1) Qué hacer (comentarios)

[Major] (Performance)  
Archivo: audittrail/views.py:L175-L180, L90-L99

Qué:
- El listado de auditoría resuelve `resolved_changes` para cada entrada y, para campos FK, ejecuta una consulta por valor (`remote_field.model.objects.filter(pk=value).first()`). Con 25 entradas por página y múltiples campos, genera N+1 consultas.

Dónde:
- `for entry in entries: entry.resolved_changes = self.resolve_entry_changes(entry)`.
- `_format_value` consulta el modelo relacionado en cada iteración.

Por qué:
- Impacta tiempos y carga de DB en páginas de auditoría; no hay caché ni `select_related` sobre los modelos auditados.

Cómo arreglar:
- Cachear por `(field.model, pk)` dentro del request o resolver en bulk antes del bucle.

```python
# en AuditLogResolveMixin.resolve_entry_changes
fk_cache = {}
...
if fk_key not in fk_cache:
    fk_cache[fk_key] = field.remote_field.model.objects.in_bulk([value]).get(value)
obj = fk_cache[fk_key]
return str(obj) if obj else f"{model_name} #{value}"
```

[Major] (Data)  
Archivo: comedores/views.py:L326-L344, L742-L765

Qué:
- `form_valid` guarda el comedor (crea historial) y luego intenta cargar imágenes; si `create_imagenes` lanza excepción, se retorna `form_invalid` sin revertir el alta/edición. El objeto queda persistido con estado/historial, pero la UI reporta error.

Dónde:
- Se ejecuta `self.object = form.save()` antes del bloque de carga de imágenes; las excepciones devuelven `form_invalid(form)`.

Por qué:
- Inconsistencia entre UI y BD, riesgo de duplicados al reintentar y registros huérfanos de historial/adjuntos.

Cómo arreglar:
- Envolver todo el `form_valid` en `transaction.atomic()` y capturar errores de imágenes para marcarlos en el form en vez de abortar tarde.

```python
from django.db import transaction
...
with transaction.atomic():
    self.object = form.save()
    for imagen in imagenes:
        try:
            ComedorService.create_imagenes(imagen, self.object.pk)
        except Exception as exc:
            form.add_error(None, f"Error cargando imagen: {exc}")
            raise
return super().form_valid(form)
```

## 4) Checklist final (resumen)
- Riesgos críticos: N+1 en auditoría ([Major/Performance]); operaciones de comedor no atómicas ([Major/Data]).
- Migraciones: no hay.
- ORM: faltan `select_related/prefetch` o caché en resolución de auditoría.
- Transacciones: faltan `transaction.atomic()` en creación/edición de comedor.
- Seguridad: sin hallazgos nuevos (no se tocan permisos/validaciones).
- Performance: principal N+1 en auditoría; no hay paginación adicional ni cache.
- Observabilidad: sin logs adicionales; sería útil loggear fallos de carga de imágenes.
- Maintainability: funciones acotadas; falta test para `ComedorForm.save` preservando `ultimo_estado`.
- Tests mínimos a exigir: (1) creación de comedor con/ sin fallo de imagen en bloque atómico; (2) resolución de cambios de auditoría no multiplica consultas (usar assertNumQueries); (3) `ComedorForm` mantiene `ultimo_estado` cuando no cambian estados.
- Refactors rápidos (≤15 min): caché de FK en `resolve_entry_changes`; agregar `transaction.atomic` en `form_valid`.
- Refactors estructurales: extraer servicio de carga de imágenes con manejo de transacciones y errores.

## 5) Apéndice (comandos útiles)
- Diff: `git diff --stat origin/development...origin/Fix_EliminacionEstados`
- Migraciones: `python manage.py showmigrations`
- N+1: revisar bucles sobre QuerySets sin `select_related/prefetch_related`.
