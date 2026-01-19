# Checklist de Verificación - Lógica de Aceptación por Rol

## ✅ Verificación de Implementación

### 1. Validación de Rol en `reservar_slot()`
- [x] Validación agregada en `cupo_service.py`
- [x] Responsables puros retornan False
- [x] Beneficiarios pueden ocupar cupo
- [x] Beneficiarios y Responsables pueden ocupar cupo
- [x] Estado se actualiza a NO_EVAL si es responsable puro

**Archivo**: `celiaquia/services/cupo_service.py` (línea ~50-60)

---

### 2. Lógica de Cruce SINTYS
- [x] Responsables puros se saltan en el cruce
- [x] Beneficiarios se incluyen en el cruce
- [x] Beneficiarios y Responsables se incluyen en el cruce
- [x] No se agregan responsables a matched_ids

**Archivo**: `celiaquia/services/cruce_service.py` (línea ~400-410)

---

### 3. Actualización de Rol en Reprocesamiento
- [x] Se detecta cuando rol cambia
- [x] Se actualiza de RESPONSABLE a BENEFICIARIO_Y_RESPONSABLE
- [x] Se guarda correctamente en BD
- [x] Se limpia el error anterior

**Archivo**: `celiaquia/views/expediente.py` (línea ~1200-1210)

---

### 4. Visualización en Expediente Detail
- [x] Se muestra correctamente el tipo de legajo
- [x] Se buscan hijos para BENEFICIARIO_Y_RESPONSABLE
- [x] Se incluyen en responsables_legajos
- [x] Se muestran "Tiene X hijo a cargo"

**Archivo**: `celiaquia/views/expediente.py` (línea ~300-350)

---

## 🧪 Casos de Prueba - Verificación Manual

### Caso 1: Solo Beneficiario - Aceptado
- [ ] Crear expediente con beneficiario
- [ ] Validar técnicamente como APROBADO
- [ ] Cruzar con SINTYS como MATCH
- [ ] Verificar: estado_cupo=DENTRO, es_titular_activo=True
- [ ] Verificar: Ocupa 1 cupo

**Resultado Esperado**: ✅ ACEPTADO

---

### Caso 2: Solo Responsable - Aceptado sin Cupo
- [ ] Crear expediente con responsable
- [ ] Verificar: NO se valida técnicamente
- [ ] Verificar: NO se incluye en cruce SINTYS
- [ ] Verificar: estado_cupo=NO_EVAL, es_titular_activo=False
- [ ] Verificar: NO ocupa cupo

**Resultado Esperado**: ✅ ACEPTADO (sin cupo)

---

### Caso 3: Beneficiario y Responsable - Aceptado
- [ ] Crear expediente con beneficiario_y_responsable
- [ ] Validar técnicamente como APROBADO
- [ ] Cruzar con SINTYS como MATCH
- [ ] Verificar: estado_cupo=DENTRO, es_titular_activo=True
- [ ] Verificar: Ocupa 1 cupo
- [ ] Verificar: Puede ser responsable de hijos

**Resultado Esperado**: ✅ ACEPTADO (con cupo)

---

### Caso 4: Responsable → Beneficiario y Responsable
- [ ] Importar como RESPONSABLE
- [ ] Reprocesar detectando beneficiario_y_responsable
- [ ] Verificar: Rol actualizado a BENEFICIARIO_Y_RESPONSABLE
- [ ] Validar técnicamente como APROBADO
- [ ] Cruzar con SINTYS como MATCH
- [ ] Verificar: estado_cupo=DENTRO, es_titular_activo=True

**Resultado Esperado**: ✅ ACEPTADO (con cupo)

---

### Caso 5: Responsable con Hijos
- [ ] Crear responsable (rol=RESPONSABLE)
- [ ] Crear hijo 1 (rol=BENEFICIARIO)
- [ ] Crear hijo 2 (rol=BENEFICIARIO)
- [ ] Validar hijos como APROBADO
- [ ] Cruzar hijos como MATCH
- [ ] Verificar: Responsable NO ocupa cupo
- [ ] Verificar: Hijo 1 ocupa 1 cupo
- [ ] Verificar: Hijo 2 ocupa 1 cupo
- [ ] Verificar: Total 2 cupos

**Resultado Esperado**: ✅ ACEPTADOS (2 cupos)

---

### Caso 6: Beneficiario No Matchea
- [ ] Crear beneficiario
- [ ] Validar como APROBADO
- [ ] Cruzar como NO_MATCH
- [ ] Verificar: estado_cupo=FUERA, es_titular_activo=False
- [ ] Verificar: NO ocupa cupo (lista de espera)

**Resultado Esperado**: ⏳ EN LISTA DE ESPERA

---

### Caso 7: Beneficiario Rechazado
- [ ] Crear beneficiario
- [ ] Validar como RECHAZADO
- [ ] Verificar: NO se incluye en cruce SINTYS
- [ ] Verificar: estado_cupo=NO_EVAL, es_titular_activo=False

**Resultado Esperado**: ❌ RECHAZADO

---

### Caso 8: Beneficiario que Ya Ocupa Cupo
- [ ] Crear beneficiario en Provincia A (DENTRO)
- [ ] Crear mismo beneficiario en Provincia B
- [ ] Validar como APROBADO
- [ ] Cruzar como MATCH
- [ ] Verificar: Provincia A: DENTRO (1 cupo)
- [ ] Verificar: Provincia B: FUERA (lista de espera)

**Resultado Esperado**: ⏳ EN LISTA DE ESPERA EN PROVINCIA B

---

### Caso 9: Responsable en Provincia A, Beneficiario en Provincia B
- [ ] Crear responsable en Provincia A (NO ocupa cupo)
- [ ] Crear mismo ciudadano como beneficiario en Provincia B
- [ ] Validar como APROBADO
- [ ] Cruzar como MATCH
- [ ] Verificar: Provincia A: NO_EVAL (0 cupo)
- [ ] Verificar: Provincia B: DENTRO (1 cupo)

**Resultado Esperado**: ✅ ACEPTADO EN AMBAS (roles diferentes)

---

### Caso 10: Responsable Puro No Ocupa Cupo
- [ ] Crear responsable
- [ ] Validar como APROBADO (si se valida)
- [ ] Cruzar como MATCH (si se cruza)
- [ ] Verificar: estado_cupo=NO_EVAL, es_titular_activo=False
- [ ] Verificar: NO ocupa cupo (incluso si APROBADO+MATCH)

**Resultado Esperado**: ✅ NO OCUPA CUPO

---

## 📊 Matriz de Verificación Rápida

| Caso | Rol | Validación | Cruce | Cupo | Estado | Resultado |
|------|-----|-----------|-------|------|--------|-----------|
| 1 | BENEFICIARIO | APROBADO | MATCH | DENTRO | ✅ | Aceptado |
| 2 | RESPONSABLE | - | - | NO_EVAL | ✅ | Aceptado |
| 3 | BENEFICIARIO_Y_RESPONSABLE | APROBADO | MATCH | DENTRO | ✅ | Aceptado |
| 4 | RESPONSABLE→BENEFICIARIO_Y_RESPONSABLE | APROBADO | MATCH | DENTRO | ✅ | Aceptado |
| 5 | RESPONSABLE + 2 BENEFICIARIOS | APROBADO | MATCH | 2 DENTRO | ✅ | Aceptados |
| 6 | BENEFICIARIO | APROBADO | NO_MATCH | FUERA | ⏳ | Lista espera |
| 7 | BENEFICIARIO | RECHAZADO | - | NO_EVAL | ❌ | Rechazado |
| 8 | BENEFICIARIO (Prov B) | APROBADO | MATCH | FUERA | ⏳ | Lista espera |
| 9 | RESPONSABLE (A) + BENEFICIARIO (B) | APROBADO | MATCH | 1 DENTRO | ✅ | Aceptados |
| 10 | RESPONSABLE | APROBADO | MATCH | NO_EVAL | ✅ | No ocupa cupo |

---

## 🔍 Verificación de Código

### Verificar en `cupo_service.py`
```python
# Línea ~50-60
if legajo.rol == ExpedienteCiudadano.ROLE_RESPONSABLE:
    if legajo.estado_cupo != EstadoCupo.NO_EVAL or legajo.es_titular_activo:
        legajo.estado_cupo = EstadoCupo.NO_EVAL
        legajo.es_titular_activo = False
        legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])
    return False
```

- [ ] Validación presente
- [ ] Retorna False para responsables
- [ ] Actualiza estado_cupo a NO_EVAL
- [ ] Actualiza es_titular_activo a False

---

### Verificar en `cruce_service.py`
```python
# Línea ~400-410
if es_responsable:
    # NO agregar a matched_ids ni unmatched_ids
    # El responsable no consume cupo
    continue
```

- [ ] Responsables se saltan
- [ ] NO se agregan a matched_ids
- [ ] NO se agregan a unmatched_ids
- [ ] Comentario explícito

---

### Verificar en `expediente.py`
```python
# Línea ~1200-1210
if not created and legajo.rol != rol_beneficiario:
    legajo.rol = rol_beneficiario
    legajo.save(update_fields=["rol"])
```

- [ ] Se detecta cambio de rol
- [ ] Se actualiza el rol
- [ ] Se guarda en BD

---

## 📋 Documentación Generada

- [x] `ANALISIS_ESCENARIOS_ACEPTACION.md` - Análisis detallado
- [x] `RESUMEN_VALIDACION_ROLES.md` - Resumen de cambios
- [x] `CASOS_PRUEBA_ACEPTACION.md` - 11 casos de prueba
- [x] `RESUMEN_EJECUTIVO_ACEPTACION.md` - Resumen ejecutivo
- [x] `DIAGRAMAS_FLUJO_ACEPTACION.md` - Diagramas visuales
- [x] `CHECKLIST_VERIFICACION_ACEPTACION.md` - Este documento

---

## ✨ Conclusión

- [x] Validación de rol implementada
- [x] Lógica de cruce verificada
- [x] Actualización de rol verificada
- [x] Visualización verificada
- [x] Documentación completa
- [x] Casos de prueba documentados
- [x] Diagramas de flujo creados

**Estado**: ✅ LISTO PARA TESTING

---

## 📞 Próximos Pasos

1. [ ] Ejecutar casos de prueba manual
2. [ ] Crear tests automatizados
3. [ ] Revisar con el equipo
4. [ ] Capacitar a usuarios
5. [ ] Monitorear en producción

---

## 📝 Notas

- Todos los cambios son **mínimos y enfocados**
- No se modificó lógica existente innecesariamente
- Se agregó validación explícita donde faltaba
- Documentación completa para referencia futura
