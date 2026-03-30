# Cambio: departamento IPI en Centro de Infancia

## Qué cambia

- Se incorpora el modelo `DepartamentoIpi` en `centrodeinfancia` como catálogo específico para el dominio IPI.
- `CentroDeInfancia` agrega el campo opcional `departamento` como `ForeignKey` a `DepartamentoIpi`.
- Se valida que el `departamento` seleccionado pertenezca a la `provincia` elegida.
- El formulario, detalle, listado, exportación CSV y admin de `CentroDeInfancia` muestran el nuevo campo.
- El formulario de `CentroDeInfancia` muestra además `decil_ipi` en un campo no editable a continuación de `departamento`.
- La vista de detalle de `CentroDeInfancia` expone el `decil_ipi` resuelto desde el departamento asociado.
- Se agrega el fixture `centrodeinfancia/fixtures/departamento_ipi.json` con 526 registros generados desde el archivo `.xlsx` provisto.

## Decisión de diseño

- El catálogo se implementa en `centrodeinfancia` y no en `core` porque por ahora responde a una tabla específica del dominio IPI y no a una taxonomía geográfica transversal del sistema.
- `provincia` en `DepartamentoIpi` referencia a `core.Provincia` para evitar duplicar la entidad provincial y facilitar filtros/consistencias con el resto del repo.
- La carga inicial se entrega como fixture para integrarse con el flujo existente de `load_fixtures` del repo y evitar un comando específico de única ocasión.
- `decil_ipi` no se persiste en `CentroDeInfancia`: se resuelve siempre desde la información del `DepartamentoIpi` seleccionado para evitar duplicación y desincronización de datos.

## Alcance explícitamente no incluido

- No se modifica `FormularioCDI`.
- No se ejecuta una carga automática en migración.

## Carga futura sugerida

1. Si cambia la fuente IPI, regenerar el fixture a partir del `.xlsx` actualizado.
2. Verificar que las provincias del archivo coincidan con `core_provincia`.
3. Cargar fixtures con el flujo habitual del repo:

```bash
docker compose exec django python manage.py load_fixtures --force
```

4. Validar que `centrodeinfancia_departamentoipi` quede poblada y que el formulario de CDI filtre correctamente por provincia.
