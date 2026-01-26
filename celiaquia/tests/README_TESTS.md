# Tests Completos de Celíacos

## Cobertura Total del Sistema

Este conjunto de tests verifica **TODO** el sistema de celíacos incluyendo el historial completo de cada operación.

## Tests de Casos de Negocio

### ✅ CASO A: Responsable = Beneficiario
- Adulto independiente que es beneficiario y responsable de sí mismo
- **Verifica**: Rol `beneficiario_y_responsable`, no auto-referencia en GrupoFamiliar
- **Historial**: Importación, asignación de cupo, movimientos

### ✅ CASO B: Responsable ≠ Beneficiario  
- Menor con responsable adulto
- **Verifica**: Roles separados, creación de GrupoFamiliar, solo beneficiario ocupa cupo
- **Historial**: Relación familiar, comentarios de validación

### ✅ CASO C: Responsable Múltiple
- Un responsable con varios beneficiarios
- **Verifica**: Múltiples relaciones familiares, cupos independientes
- **Historial**: Todas las relaciones registradas correctamente

### ✅ CASO D: Solo Beneficiario
- Beneficiario adulto sin responsable
- **Verifica**: Sin GrupoFamiliar, ocupa cupo normalmente
- **Historial**: Proceso completo sin responsable

### ✅ CASO E: Menor como Responsable
- Beneficiario menor de 18 años como responsable
- **Verifica**: Warning generado, permite continuar
- **Historial**: Warning registrado en sistema

### ✅ ERROR 1: Responsable más joven
- Responsable con fecha de nacimiento posterior al beneficiario
- **Verifica**: Rechazo total, no se crea nada
- **Historial**: Error registrado en RegistroErroneo

### ✅ ERROR 2: Documento inválido
- Documento con formato incorrecto
- **Verifica**: Validación de formato, rechazo
- **Historial**: Error de validación registrado

## Tests de Flujo Completo

### ✅ FLUJO COMPLETO CON HISTORIAL TOTAL
**El test más importante - Verifica TODO el sistema:**

#### 1. Importación
- Carga desde Excel
- Validación de datos
- Creación de ciudadanos y legajos
- **Historial**: ExpedienteEstadoHistorial (CREADO → PROCESADO)

#### 2. Asignación de Técnico
- Asignación de técnico al expediente
- **Historial**: AsignacionTecnico con estado activo

#### 3. Carga de Documentos
- Creación de TipoDocumento
- Carga de DNI y Certificado Médico
- **Historial**: DocumentoLegajo con usuario y fecha
- **Historial**: HistorialComentarios tipo OBSERVACION_GENERAL

#### 4. Validación Técnica con Subsanación
- **Matias**: Aprobado directo
  - Comentario de validación
  - Estado APROBADO
- **Juan**: Requiere subsanación
  - Comentario de motivo de subsanación
  - Estado SUBSANAR
  - Respuesta del ciudadano con archivo
  - Estado SUBSANADO
  - Aprobación final
- **Historial**: 
  - HistorialComentarios (VALIDACION_TECNICA, SUBSANACION_MOTIVO, SUBSANACION_RESPUESTA)
  - HistorialValidacionTecnica con cambios de estado

#### 5. Cruce SINTYS
- Validación con organismo externo
- **Historial**: HistorialComentarios tipo CRUCE_SINTYS

#### 6. Asignación de Cupos
- Evaluación de cupo disponible
- Asignación de cupo DENTRO
- **Historial**: 
  - HistorialCupo con tipo_movimiento ALTA
  - CupoMovimiento con delta +1
  - ProvinciaCupo.usados actualizado

#### 7. Cambio de Estado de Expediente
- PROCESADO → PAGO_ABIERTO
- **Historial**: ExpedienteEstadoHistorial

#### 8. Generación de Pago
- Creación de PagoExpediente
- Generación de PagoNomina
- **Historial**: HistorialComentarios tipo PAGO_OBSERVACION

#### Verificaciones de Historial:
- ✅ Historial de estados de expediente (mínimo 2 cambios)
- ✅ Historial de validación técnica por legajo
- ✅ Historial de cupos con movimientos ALTA
- ✅ Historial de comentarios completo (mínimo 4 por legajo)
- ✅ Tipos de comentarios esperados presentes
- ✅ Movimientos de cupo registrados (2 ALTA)
- ✅ Documentos con historial completo (4 total)
- ✅ Asignaciones de técnico activas
- ✅ Nómina de pago generada (2 beneficiarios)
- ✅ Cupo provincial actualizado correctamente

#### Verificaciones de Trazabilidad:
- ✅ Orden cronológico de comentarios
- ✅ Fechas en secuencia correcta
- ✅ Sin comentarios huérfanos
- ✅ Sin movimientos huérfanos
- ✅ Sin documentos huérfanos
- ✅ Integridad referencial completa

### ✅ HISTORIAL CON ERRORES Y RECUPERACIÓN
**Verifica el manejo completo de errores y recuperación:**

#### Escenario:
1. **Documento Rechazado**
   - Carga de DNI con problemas
   - Técnico rechaza: RECHAZADO
   - **Historial**: Comentario de rechazo

2. **Solicitud de Subsanación**
   - Técnico solicita corrección
   - Estado: SUBSANAR
   - **Historial**: Motivo de subsanación

3. **Ciudadano Responde**
   - Carga documento corregido (reemplaza anterior)
   - Comentario de respuesta
   - Estado: SUBSANADO
   - **Historial**: Respuesta con archivo adjunto

4. **Aprobación Final**
   - Técnico aprueba documento corregido
   - Estado: APROBADO
   - **Historial**: Comentario de aprobación

5. **Cruce con Error**
   - Primer intento: Error de conexión
   - Estado: SIN_CRUCE
   - **Historial**: Comentario de error

6. **Reintento Exitoso**
   - Segundo intento: Exitoso
   - Estado: MATCH
   - **Historial**: Comentario de éxito

7. **Suspensión Temporal**
   - Beneficiario suspendido
   - Estado cupo: DENTRO, es_titular_activo: False
   - **Historial**: Movimiento SUSPENDIDO (delta 0)

8. **Reactivación**
   - Beneficiario reactivado
   - Estado cupo: DENTRO, es_titular_activo: True
   - **Historial**: Movimiento REACTIVACION (delta 0)

#### Verificaciones:
- ✅ Secuencia completa de comentarios (mínimo 8)
- ✅ Todos los tipos de comentarios presentes
- ✅ Documentos reemplazados correctamente (2 finales)
- ✅ Movimientos de cupo: ALTA + SUSPENDIDO + REACTIVACION
- ✅ Estados finales correctos
- ✅ Trazabilidad temporal mantenida
- ✅ Cada cambio de estado generó comentario
- ✅ Integridad de datos completa
- ✅ Todos los movimientos tienen motivo
- ✅ Todos los comentarios tienen contexto

### ✅ LÍMITE CUPO PROVINCIAL
- Verifica límites de cupo por provincia
- **Historial**: Solo los que entran en cupo tienen movimiento ALTA
- **Historial**: Los que quedan fuera no tienen movimiento

## Tests de Servicios

### ✅ Servicio de Comentarios
- Agregar comentarios de todos los tipos
- Obtener historial completo
- Filtrar por tipo de comentario
- **Verifica**: Todos los comentarios se registran con usuario y fecha

### ✅ Servicio de Documentos
- Crear tipos de documento
- Agregar documentos
- Verificar completitud
- Reemplazar documentos
- **Verifica**: Historial de carga con usuario y observaciones

### ✅ Servicio de Asignaciones
- Asignar técnico
- Reasignar técnico (desactiva anterior)
- Desasignar técnico
- Obtener historial de asignaciones
- **Verifica**: Campo activa funciona correctamente

### ✅ Integración de Servicios
- Todos los servicios trabajando juntos
- Comentarios automáticos al cargar documentos
- Trazabilidad completa
- **Verifica**: Integración sin conflictos

### ✅ Signals Automáticos
- Cambios de estado generan comentarios automáticos
- Subsanaciones registradas automáticamente
- **Verifica**: Signals funcionan sin intervención manual

## Ejecución de Tests

### Ejecutar todos los tests:
```bash
python manage.py ejecutar_tests_completos
```

### Solo casos de negocio:
```bash
python manage.py ejecutar_tests_completos --solo-casos
```

### Solo servicios:
```bash
python manage.py ejecutar_tests_completos --solo-servicios
```

### Test específico:
```bash
python manage.py test celiaquia.tests.test_casos_completos_celiaquia.CeliacosTestCompleto.test_flujo_completo_con_historial_completo
```

## Cobertura Verificada

### ✅ Modelos
- Expediente
- ExpedienteCiudadano
- EstadoExpediente
- EstadoLegajo
- ProvinciaCupo
- CupoMovimiento
- PagoExpediente
- PagoNomina
- HistorialComentarios
- HistorialValidacionTecnica
- HistorialCupo
- TipoDocumento
- DocumentoLegajo
- AsignacionTecnico
- RegistroErroneo
- RegistroErroneoReprocesado

### ✅ Servicios
- ImportacionService
- CupoService
- PagoService
- ComentariosService
- DocumentosService
- AsignacionService

### ✅ Roles
- beneficiario
- responsable
- beneficiario_y_responsable

### ✅ Estados de Expediente
- CREADO
- PROCESADO
- PAGO_ABIERTO

### ✅ Estados de Legajo
- DOCUMENTO_PENDIENTE
- ARCHIVO_CARGADO

### ✅ Estados de Revisión Técnica
- PENDIENTE
- APROBADO
- RECHAZADO
- SUBSANAR
- SUBSANADO

### ✅ Resultados SINTYS
- SIN_CRUCE
- MATCH
- NO_MATCH

### ✅ Estados de Cupo
- NO_EVAL
- DENTRO
- FUERA

### ✅ Tipos de Movimiento de Cupo
- ALTA
- BAJA
- SUSPENDIDO
- REACTIVACION
- AJUSTE

### ✅ Tipos de Comentarios
- VALIDACION_TECNICA
- SUBSANACION_MOTIVO
- SUBSANACION_RESPUESTA
- RENAPER_VALIDACION
- OBSERVACION_GENERAL
- CRUCE_SINTYS
- PAGO_OBSERVACION

## Métricas de Cobertura

- **Casos de negocio**: 10 tests
- **Servicios**: 5 tests
- **Total**: 15 tests
- **Líneas de código de test**: ~1500
- **Tiempo estimado**: ~30-60 segundos

## Garantías del Test

✅ **Proceso Real**: Usa servicios reales, no mocks
✅ **Base de Datos Real**: Crea y verifica datos reales
✅ **Archivos Reales**: Genera Excel reales
✅ **Historial Completo**: Verifica cada cambio registrado
✅ **Trazabilidad**: Orden cronológico verificado
✅ **Integridad**: Sin datos huérfanos
✅ **Recuperación**: Manejo de errores completo
✅ **Cupos**: Límites y movimientos verificados
✅ **Pagos**: Nóminas generadas correctamente
✅ **Documentos**: Sistema normalizado funcional
✅ **Comentarios**: Historial completo de subsanaciones

## Conclusión

Este conjunto de tests garantiza que **TODO** el sistema de celíacos funciona correctamente, incluyendo:
- Importación masiva
- Validación técnica
- Subsanaciones
- Cruces con organismos
- Gestión de cupos
- Generación de pagos
- **Historial completo de TODAS las operaciones**
- **Trazabilidad total de cambios**
- **Integridad referencial**
- **Manejo de errores y recuperación**