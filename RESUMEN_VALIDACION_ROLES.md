# Resumen de Cambios - Validación de Aceptación por Rol

## Problema Identificado
La lógica de aceptación al programa no validaba correctamente el rol del ciudadano. Específicamente:
- **Responsables puros** (`ROLE_RESPONSABLE`) podrían ocupar cupo incorrectamente
- No había validación explícita del rol en `reservar_slot()`

## Solución Implementada

### 1. Validación en `cupo_service.py` - `reservar_slot()`
**Archivo**: `c:\Users\usuar\BACKOFFICE\celiaquia\services\cupo_service.py`

**Cambio**: Agregada validación de rol ANTES de validar APROBADO + MATCH

```python
# Validar que califica para cupo: debe ser beneficiario (no responsable puro)
if legajo.rol == ExpedienteCiudadano.ROLE_RESPONSABLE:
    if legajo.estado_cupo != EstadoCupo.NO_EVAL or legajo.es_titular_activo:
        legajo.estado_cupo = EstadoCupo.NO_EVAL
        legajo.es_titular_activo = False
        legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])
    return False
```

**Lógica**:
- Si el rol es `RESPONSABLE` → NO puede ocupar cupo → retorna False
- Si el rol es `BENEFICIARIO` o `BENEFICIARIO_Y_RESPONSABLE` → puede intentar ocupar cupo
- Además debe cumplir: `APROBADO + MATCH`

### 2. Validación en `cruce_service.py` - `procesar_cruce_por_cuit()`
**Archivo**: `c:\Users\usuar\BACKOFFICE\celiaquia\services\cruce_service.py`

**Estado**: ✅ Ya implementado correctamente

```python
# Si es responsable, NO asignarle cupo a él, solo validar para sus hijos
if es_responsable:
    # NO agregar a matched_ids ni unmatched_ids
    # El responsable no consume cupo
    continue
```

**Lógica**:
- Responsables puros se saltan en el cruce (no se agregan a matched_ids)
- No consumen cupo
- Solo sus hijos (beneficiarios) consumen cupo

### 3. Actualización de Rol en `expediente.py` - `ReprocesarRegistrosErroneosView`
**Archivo**: `c:\Users\usuar\BACKOFFICE\celiaquia\views\expediente.py`

**Estado**: ✅ Ya implementado correctamente

```python
# Si ya existía, actualizar el rol si cambió
if not created and legajo.rol != rol_beneficiario:
    legajo.rol = rol_beneficiario
    legajo.save(update_fields=["rol"])
```

**Lógica**:
- Permite que un responsable se convierta en beneficiario_y_responsable
- Actualiza el rol si cambió durante el reprocesamiento

---

## Matriz de Validación Final

| Escenario | Rol | ¿Aprobado? | ¿Match? | ¿Ocupa Cupo? | Estado Cupo | Titular Activo |
|-----------|-----|-----------|---------|-------------|-------------|----------------|
| Solo Beneficiario | BENEFICIARIO | ✅ Sí | ✅ Sí | ✅ Sí | DENTRO | True |
| Solo Beneficiario | BENEFICIARIO | ✅ Sí | ❌ No | ❌ No | FUERA | False |
| Solo Beneficiario | BENEFICIARIO | ❌ No | - | ❌ No | NO_EVAL | False |
| Solo Responsable | RESPONSABLE | ✅ Sí | ✅ Sí | ❌ No | NO_EVAL | False |
| Solo Responsable | RESPONSABLE | ✅ Sí | ❌ No | ❌ No | NO_EVAL | False |
| Beneficiario y Responsable | BENEFICIARIO_Y_RESPONSABLE | ✅ Sí | ✅ Sí | ✅ Sí | DENTRO | True |
| Beneficiario y Responsable | BENEFICIARIO_Y_RESPONSABLE | ✅ Sí | ❌ No | ❌ No | FUERA | False |
| Beneficiario y Responsable | BENEFICIARIO_Y_RESPONSABLE | ❌ No | - | ❌ No | NO_EVAL | False |

---

## Flujos de Aceptación

### Flujo 1: Beneficiario Simple
```
1. Importación → rol=BENEFICIARIO
2. Validación técnica → APROBADO
3. Cruce SINTYS → MATCH
4. reservar_slot() → ✅ Ocupa cupo (DENTRO, es_titular_activo=True)
```

### Flujo 2: Responsable Simple
```
1. Importación → rol=RESPONSABLE
2. Validación técnica → (no se valida, es responsable)
3. Cruce SINTYS → (se salta, es responsable)
4. reservar_slot() → ❌ NO ocupa cupo (NO_EVAL, es_titular_activo=False)
```

### Flujo 3: Beneficiario y Responsable
```
1. Importación → rol=RESPONSABLE (inicialmente)
2. Reprocesamiento → rol=BENEFICIARIO_Y_RESPONSABLE (se actualiza)
3. Validación técnica → APROBADO
4. Cruce SINTYS → MATCH
5. reservar_slot() → ✅ Ocupa cupo (DENTRO, es_titular_activo=True)
```

### Flujo 4: Responsable con Hijos
```
Responsable:
1. rol=RESPONSABLE
2. NO ocupa cupo (NO_EVAL)

Hijo 1:
1. rol=BENEFICIARIO
2. APROBADO + MATCH → Ocupa 1 cupo

Hijo 2:
1. rol=BENEFICIARIO
2. APROBADO + MATCH → Ocupa 1 cupo

Total: 2 cupos (solo los hijos)
```

---

## Validaciones Implementadas

✅ **En `reservar_slot()`**: Valida que el rol sea beneficiario antes de intentar ocupar cupo
✅ **En `procesar_cruce_por_cuit()`**: Salta responsables puros en el cruce
✅ **En `ReprocesarRegistrosErroneosView`**: Actualiza el rol si cambió
✅ **En `expediente_detail`**: Muestra correctamente el tipo de legajo según el rol

---

## Casos Especiales Manejados

### Caso: Responsable que se convierte en Beneficiario y Responsable
- **Antes**: rol=RESPONSABLE, estado_cupo=NO_EVAL
- **Después de reprocesamiento**: rol=BENEFICIARIO_Y_RESPONSABLE
- **Validación técnica**: Se valida (es beneficiario)
- **Cruce**: Se incluye (es beneficiario)
- **Cupo**: Ocupa cupo si APROBADO + MATCH

### Caso: Ciudadano que aparece como responsable en un expediente y beneficiario en otro
- **Expediente 1**: rol=RESPONSABLE, NO ocupa cupo
- **Expediente 2**: rol=BENEFICIARIO, ocupa cupo si APROBADO + MATCH
- **Validación**: Cada expediente se valida independientemente

### Caso: Responsable que ya ocupa cupo en otra provincia
- **Validación**: No aplica (responsables no ocupan cupo)
- **Resultado**: NO_EVAL, es_titular_activo=False

---

## Testing Recomendado

1. **Test: Responsable puro no ocupa cupo**
   - Crear legajo con rol=RESPONSABLE
   - Validar APROBADO + MATCH
   - Verificar que estado_cupo=NO_EVAL

2. **Test: Beneficiario ocupa cupo**
   - Crear legajo con rol=BENEFICIARIO
   - Validar APROBADO + MATCH
   - Verificar que estado_cupo=DENTRO

3. **Test: Beneficiario y Responsable ocupa cupo**
   - Crear legajo con rol=BENEFICIARIO_Y_RESPONSABLE
   - Validar APROBADO + MATCH
   - Verificar que estado_cupo=DENTRO

4. **Test: Responsable que se convierte en Beneficiario y Responsable**
   - Importar como RESPONSABLE
   - Reprocesar como BENEFICIARIO_Y_RESPONSABLE
   - Validar APROBADO + MATCH
   - Verificar que estado_cupo=DENTRO

---

## Conclusión

La lógica de aceptación ahora es **clara y consistente**:
- ✅ Todos se aceptan al programa (responsables, beneficiarios, ambos)
- ✅ Solo beneficiarios ocupan cupo
- ✅ Validación técnica solo para beneficiarios
- ✅ Responsables puros nunca ocupan cupo
- ✅ Beneficiarios y responsables ocupan cupo como beneficiarios
