# VALIDACIÓN DE MIGRACIONES - CELIAQUIA (100% SEGURO)

## Estrategia: SOLO ESTRUCTURA, SIN DATOS

### ¿Por qué es 100% seguro?

1. **NO migra datos automáticamente** → No hay errores silenciosos
2. **Solo crea tablas vacías** → Reversible sin pérdida
3. **Mantiene datos en ExpedienteCiudadano** → Fuente de verdad
4. **Rollback es trivial** → Solo elimina tablas nuevas

## Migración 0005 (vacía)
- Placeholder para compatibilidad

## Migración 0006 (SEGURA - solo estructura)
- Crea tabla `celiaquia_validaciontecnica` (vacía)
- Crea tabla `celiaquia_cruceresultado` (vacía)
- Crea tabla `celiaquia_cupotitular` (vacía)
- Crea tabla `celiaquia_validacionrenaper` (vacía)
- **NO migra datos** (se hace manualmente después si es necesario)

## Ejecución

```bash
# 1. Backup
mysqldump -u root -p sisoc > backup_antes_migracion.sql

# 2. Ejecutar migración
python manage.py migrate celiaquia

# 3. Verificar que las tablas existen pero están vacías
mysql -u root -p sisoc -e "SELECT COUNT(*) FROM celiaquia_validaciontecnica;"
# Debe retornar: 0
```

## Validación post-migración

### ✅ Verificar que las tablas existen

```sql
SHOW TABLES LIKE 'celiaquia_%';
-- Debe incluir:
-- celiaquia_validaciontecnica
-- celiaquia_cruceresultado
-- celiaquia_cupotitular
-- celiaquia_validacionrenaper
```

### ✅ Verificar que están vacías

```sql
SELECT COUNT(*) FROM celiaquia_validaciontecnica;
SELECT COUNT(*) FROM celiaquia_cruceresultado;
SELECT COUNT(*) FROM celiaquia_cupotitular;
SELECT COUNT(*) FROM celiaquia_validacionrenaper;
-- Todos deben retornar: 0
```

### ✅ Verificar que ExpedienteCiudadano no cambió

```sql
SELECT COUNT(*) FROM celiaquia_expedienteciudadano;
-- Debe retornar: número de legajos existentes (sin cambios)

SELECT COUNT(*) FROM celiaquia_expedienteciudadano WHERE rol IS NOT NULL;
-- Debe retornar: número de legajos (todos tienen rol='beneficiario' por defecto)
```

### ✅ Verificar que AsignacionTecnico no cambió

```sql
SELECT COUNT(*) FROM celiaquia_asignaciontecnico;
-- Debe retornar: número de asignaciones existentes (sin cambios)

SELECT COUNT(*) FROM celiaquia_asignaciontecnico WHERE activa = 1;
-- Debe retornar: número de asignaciones (todas tienen activa=True por defecto)
```

## Rollback (si es necesario)

```bash
python manage.py migrate celiaquia 0005_add_rol_and_new_models
```

Esto eliminará:
- Tabla `celiaquia_validaciontecnica`
- Tabla `celiaquia_cruceresultado`
- Tabla `celiaquia_cupotitular`
- Tabla `celiaquia_validacionrenaper`

**Resultado**: Sistema vuelve a estado anterior, sin pérdida de datos

## Migración de datos (MANUAL - después de validar)

Si todo está bien, se puede migrar datos manualmente:

```python
# En Django shell
from celiaquia.models import ExpedienteCiudadano, ValidacionTecnica, CruceResultado, CupoTitular, ValidacionRenaper

for legajo in ExpedienteCiudadano.objects.all():
    ValidacionTecnica.objects.get_or_create(
        legajo=legajo,
        defaults={
            "revision_tecnico": legajo.revision_tecnico,
            "subsanacion_motivo": legajo.subsanacion_motivo,
            "subsanacion_solicitada_en": legajo.subsanacion_solicitada_en,
            "subsanacion_enviada_en": legajo.subsanacion_enviada_en,
            "subsanacion_usuario": legajo.subsanacion_usuario,
        }
    )
    # ... repetir para otros modelos
```

## Ventajas de esta estrategia

| Aspecto | Beneficio |
|--------|----------|
| **Seguridad** | 100% - No hay migración automática de datos |
| **Reversibilidad** | Total - Rollback elimina solo tablas nuevas |
| **Compatibilidad** | Completa - Compatible con main |
| **Validación** | Fácil - Tablas vacías son obvias |
| **Control** | Total - Migración de datos es manual y controlada |

## Checklist final

- [ ] Backup realizado
- [ ] Migración ejecutada sin errores
- [ ] Tablas nuevas existen y están vacías
- [ ] ExpedienteCiudadano no cambió
- [ ] AsignacionTecnico no cambió
- [ ] Rollback probado (opcional)
- [ ] Sistema funciona normalmente

## Conclusión

Esta migración es **100% segura** porque:
1. ✅ No modifica datos existentes
2. ✅ Solo crea estructura nueva
3. ✅ Rollback es trivial
4. ✅ Compatible con main
5. ✅ Fácil de validar
