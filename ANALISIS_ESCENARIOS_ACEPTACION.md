# Análisis de Escenarios de Aceptación al Programa

## Contexto
El sistema maneja tres roles para ciudadanos en un expediente:
- **BENEFICIARIO**: Solo recibe prestaciones (hijo/a)
- **RESPONSABLE**: Solo es responsable legal (no recibe prestaciones)
- **BENEFICIARIO_Y_RESPONSABLE**: Es ambos (responsable que también recibe prestaciones)

## Escenarios de Aceptación

### Escenario 1: Solo Beneficiario
**Datos**: Persona que solo aparece como beneficiario
- **Rol**: `BENEFICIARIO`
- **Aceptación**: ✅ Se acepta al programa
- **Cupo**: ✅ Ocupa 1 cupo (es titular)
- **Validación**: Debe estar APROBADO + MATCH
- **Resultado**: `estado_cupo=DENTRO`, `es_titular_activo=True`

**Ejemplo**: Niño/a que recibe prestaciones

---

### Escenario 2: Solo Responsable
**Datos**: Persona que solo es responsable legal
- **Rol**: `RESPONSABLE`
- **Aceptación**: ✅ Se acepta al programa (como responsable)
- **Cupo**: ❌ NO ocupa cupo (no es beneficiario)
- **Validación**: No requiere validación técnica (no es beneficiario)
- **Resultado**: `estado_cupo=NO_EVAL`, `es_titular_activo=False`

**Ejemplo**: Padre/madre que solo firma documentos

---

### Escenario 3: Beneficiario y Responsable
**Datos**: Persona que es responsable Y recibe prestaciones
- **Rol**: `BENEFICIARIO_Y_RESPONSABLE`
- **Aceptación**: ✅ Se acepta al programa
- **Cupo**: ✅ Ocupa 1 cupo (es titular como beneficiario)
- **Validación**: Debe estar APROBADO + MATCH
- **Resultado**: `estado_cupo=DENTRO`, `es_titular_activo=True`

**Ejemplo**: Madre que es responsable de sus hijos pero también recibe prestaciones

---

## Matriz de Decisión

| Rol | ¿Se Acepta? | ¿Ocupa Cupo? | Validación Requerida | Estado Cupo | Titular Activo |
|-----|-------------|--------------|----------------------|-------------|----------------|
| BENEFICIARIO | ✅ Sí | ✅ Sí | APROBADO + MATCH | DENTRO | True |
| RESPONSABLE | ✅ Sí | ❌ No | No | NO_EVAL | False |
| BENEFICIARIO_Y_RESPONSABLE | ✅ Sí | ✅ Sí | APROBADO + MATCH | DENTRO | True |

---

## Validaciones Implementadas

### En `reservar_slot()` (cupo_service.py)
```python
# Validar que califica para cupo: debe ser beneficiario (no responsable puro)
if legajo.rol == ExpedienteCiudadano.ROLE_RESPONSABLE:
    # Responsable puro no ocupa cupo
    return False
```

**Lógica**:
1. Si el rol es `RESPONSABLE` → NO ocupa cupo → retorna False
2. Si el rol es `BENEFICIARIO` o `BENEFICIARIO_Y_RESPONSABLE` → puede ocupar cupo
3. Además debe cumplir: `APROBADO + MATCH`

---

## Casos de Uso Complejos

### Caso A: Responsable que luego se convierte en Beneficiario
**Escenario**: Se importa primero como responsable, luego se reprocesa y se detecta que es beneficiario_y_responsable

**Flujo**:
1. Importación inicial: `rol=RESPONSABLE`, `estado_cupo=NO_EVAL`
2. Reprocesamiento: `rol=BENEFICIARIO_Y_RESPONSABLE` (se actualiza)
3. Validación técnica: Si APROBADO + MATCH → `reservar_slot()` lo acepta
4. Resultado: `estado_cupo=DENTRO`, `es_titular_activo=True`

**Código que lo maneja** (expediente.py - ReprocesarRegistrosErroneosView):
```python
# Si ya existía, actualizar el rol si cambió
if not created and legajo.rol != rol_beneficiario:
    legajo.rol = rol_beneficiario
    legajo.save(update_fields=["rol"])
```

---

### Caso B: Responsable con Hijos
**Escenario**: Responsable que tiene hijos a cargo en el mismo expediente

**Flujo**:
1. Responsable: `rol=RESPONSABLE`, `estado_cupo=NO_EVAL` (no ocupa cupo)
2. Hijo 1: `rol=BENEFICIARIO`, validado → `estado_cupo=DENTRO` (ocupa 1 cupo)
3. Hijo 2: `rol=BENEFICIARIO`, validado → `estado_cupo=DENTRO` (ocupa 1 cupo)
4. Total cupo usado: 2 (solo los hijos, no el responsable)

---

### Caso C: Responsable que es Beneficiario y Responsable
**Escenario**: Responsable que también recibe prestaciones

**Flujo**:
1. Importación: `rol=RESPONSABLE`, `estado_cupo=NO_EVAL`
2. Reprocesamiento detecta que es beneficiario_y_responsable
3. Rol actualizado: `rol=BENEFICIARIO_Y_RESPONSABLE`
4. Validación técnica: Si APROBADO + MATCH → `reservar_slot()` lo acepta
5. Resultado: `estado_cupo=DENTRO`, `es_titular_activo=True` (ocupa 1 cupo)

---

## Validaciones en Vistas

### En `RevisarLegajoView` (expediente.py)
Cuando se aprueba un legajo:
```python
if accion == "APROBAR":
    leg.revision_tecnico = "APROBADO"
    leg.save(...)
    # El cupo se reserva después en el flujo de cruce/pago
```

**Nota**: La reserva de cupo ocurre típicamente después del cruce SINTYS (cuando se confirma MATCH)

---

## Resumen de Cambios

✅ **Validación de rol en `reservar_slot()`**:
- Responsables puros (`ROLE_RESPONSABLE`) NO pueden ocupar cupo
- Solo beneficiarios (`ROLE_BENEFICIARIO`, `ROLE_BENEFICIARIO_Y_RESPONSABLE`) ocupan cupo

✅ **Actualización de rol en reprocesamiento**:
- Si un legajo ya existe pero el rol cambió, se actualiza
- Permite que responsables se conviertan en beneficiario_y_responsable

✅ **Lógica de aceptación clara**:
- Todos se aceptan al programa (responsables, beneficiarios, ambos)
- Solo beneficiarios ocupan cupo
- Validación técnica solo para beneficiarios
