# Análisis de Funcionalidad: Carga de Expedientes de Pagos y Actualización de Estados de Comedores

## Fecha de Análisis
16 de abril de 2026

## Objetivo
Analizar la viabilidad de integrar la carga de expedientes de pagos de Comedores con la actualización automática de Estados y Subestados en el legajo de cada comedor, según reglas específicas de negocio.

## Contexto Actual
- **Módulo `expedientespagos`**: Gestiona expedientes de pago asociados a comedores.
- **Módulo `comedores`**: Maneja estados de comedores mediante `EstadoActividad`, `EstadoProceso`, `EstadoDetalle`, `EstadoGeneral`, `EstadoHistorial` y `Comedor.ultimo_estado`.
- **Relación existente**: Cada `ExpedientePago` está ligado a un `Comedor` via FK.
- **Flujo actual**: La carga de expedientes no afecta los estados del legajo.

## Reglas de Negocio Propuestas
1. **Campo nuevo**: Agregar `mes_convenio` en `ExpedientePago` (IntegerField con choices 1-6).
2. **Regla de actualización de estado**:
   - Si el comedor aparece en un expediente con `mes_convenio` 1-3: Estado "En ejecución", Subestado vacío.
   - Si aparece con `mes_convenio` 4-6: Estado "En ejecución", Subestado "En proceso renovación".
   - Si no aparece en el último expediente: Pasa a "En proceso renovación".
   - Si no aparece en 3 expedientes consecutivos: Estado "Inactivo", Subestado "Baja".
   - Si nunca aparece: Estado "Inactivo".
3. **Actualización global**: Cada vez que se sube un nuevo expediente, recalcular estados de TODOS los comedores (ya que la ausencia afecta a otros).
4. **Medición de ausencias**: Por cantidad de expedientes consecutivos en que el comedor no figura, no por tiempo calendario.

## Viabilidad Técnica
### Positiva
- La estructura de datos ya soporta la relación (FK existente).
- El servicio de estados `comedores.services.estado_manager.registrar_cambio_estado` ya existe y es reutilizable.
- No requiere cambios en estados disponibles ni en la cantidad de meses (fijo en 6).
- Desacopla lógica de negocio en servicios.

### Puntos Débiles
1. **Ambigüedad en secuencia de expedientes**: ¿Cómo se ordenan los "últimos 3 expedientes"? Asumiendo por `fecha_creacion` descendente.
2. **Ausencia como criterio**: Sensible a datos incompletos o errores en carga de expedientes.
3. **Rendimiento**: Recalcular estados de todos los comedores en cada carga podría ser costoso si hay muchos comedores.
4. **Dependencia de datos históricos**: Cambios en expedientes antiguos pueden alterar estados actuales.

### Alternativas Consideradas
1. **Vista/Form directa**: Llamar a `registrar_cambio_estado` desde `ExpedientesPagosCreateView.post()`.
   - Ventaja: Claro y visible.
   - Desventaja: Lógica hardcodeada en vista.

2. **Servicio centralizado**: Extender `ExpedientesPagosService` con función de cálculo de estado.
   - Ventaja: Reutilizable, mejor separación de concerns.
   - Desventaja: Más complejo.

3. **Señal post_save**: Automático, pero menos explícito.

4. **Campo explícito en ExpedientePago**: Para mapear eventos de estado, pero no necesario aquí.

### Recomendación
- Usar servicio centralizado para mantener lógica desacoplada.
- Implementar como `ExpedientesPagosService.recalcular_estados_todos_comedores()` llamado desde crear/actualizar.
- Validar orden de expedientes y consistencia.

## Implementación Propuesta
### Cambios en Modelo
- Agregar `mes_convenio` a `ExpedientePago`.

### Cambios en Servicio
- Actualizar `crear_expediente_pago` y `actualizar_expediente_pago` para incluir `mes_convenio`.
- Agregar `recalcular_estados_todos_comedores()`: Itera sobre todos los comedores.
- Agregar `recalcular_estado_comedor(comedor)`: Lógica de reglas basada en últimos 3 expedientes.

### Integración
- Llamar a recalculo después de guardar expediente.
- Usar `registrar_cambio_estado` para actualizar `Comedor.ultimo_estado`.

### Migración
- `python manage.py makemigrations expedientespagos`
- `python manage.py migrate`

### Validación
- Tests unitarios para lógica de estado.
- Pruebas de integración con carga de expedientes.

## Próximos Pasos
- Confirmar reglas y lógica con stakeholders.
- Revisar nombres exactos de estados en BD (asumidos: "En ejecución", "Inactivo", "En proceso renovación", "Baja").
- Evaluar impacto en rendimiento.
- Si aprobado, proceder con implementación.

## Notas Adicionales
- Este análisis asume que los expedientes se ordenan por `fecha_creacion` para determinar "últimos".
- La regla de "3 meses" se mide por ausencias consecutivas en expedientes, no por calendario.
- Compatible con estructura existente sin cambios en estados disponibles.