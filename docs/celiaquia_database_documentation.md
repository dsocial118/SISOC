# Documentación de Base de Datos - Proyecto Celíacos

## Índice
1. [Introducción](#introducción)
2. [Tablas Principales](#tablas-principales)
3. [Tablas de Parametría](#tablas-de-parametría)
4. [Tablas de Historial y Auditoría](#tablas-de-historial-y-auditoría)
5. [Tablas de Gestión de Cupos](#tablas-de-gestión-de-cupos)
6. [Tablas de Pagos](#tablas-de-pagos)
7. [Tablas de Validación](#tablas-de-validación)
8. [Tablas de Errores y Reprocesamiento](#tablas-de-errores-y-reprocesamiento)
9. [Relaciones entre Tablas](#relaciones-entre-tablas)
10. [Procesos de Negocio](#procesos-de-negocio)

---

## Introducción

El proyecto de Celíacos es un sistema de gestión de expedientes para el programa de asistencia alimentaria para personas celíacas. El sistema maneja el ciclo completo desde la carga de beneficiarios hasta el pago de las prestaciones, incluyendo validaciones técnicas, cruces con organismos externos y gestión de cupos provinciales.

---

## Tablas Principales

### 1. Expediente
**Propósito**: Contenedor principal que agrupa a todos los ciudadanos de una provincia para un período determinado.

**Campos principales**:
- `usuario_provincia`: Usuario que creó el expediente (FK a User)
- `usuario_modificador`: Usuario que modificó por última vez (FK a User)
- `estado`: Estado actual del expediente (FK a EstadoExpediente)
- `numero_expediente`: Número identificatorio del expediente
- `excel_masivo`: Archivo Excel con la carga masiva de ciudadanos
- `cruce_excel`: Archivo Excel con resultados de cruces
- `documento`: Documento final del expediente
- `fecha_creacion`, `fecha_modificacion`, `fecha_cierre`: Timestamps de control

**Razón de existir**: Organiza y controla el flujo de trabajo por provincia, permitiendo el seguimiento del estado general del proceso.

**Relaciones**:
- Uno a muchos con ExpedienteCiudadano
- Muchos a uno con EstadoExpediente
- Uno a muchos con ExpedienteEstadoHistorial

### 2. ExpedienteCiudadano (Legajo)
**Propósito**: Representa la participación de un ciudadano específico en un expediente, conteniendo toda la información y documentación requerida.

**Campos principales**:
- `expediente`: Expediente al que pertenece (FK a Expediente)
- `ciudadano`: Ciudadano asociado (FK a Ciudadano)
- `estado`: Estado del legajo (FK a EstadoLegajo)
- `archivo1`, `archivo2`, `archivo3`: Documentos requeridos
- `archivos_ok`: Indica si tiene la documentación completa
- `revision_tecnico`: Estado de la revisión técnica (PENDIENTE, APROBADO, RECHAZADO, SUBSANAR, SUBSANADO)
- `resultado_sintys`: Resultado del cruce con SINTYS (SIN_CRUCE, MATCH, NO_MATCH)
- `estado_cupo`: Estado respecto al cupo provincial (NO_EVAL, DENTRO, FUERA)
- `es_titular_activo`: Indica si es titular activo del beneficio
- `rol`: Rol del ciudadano (beneficiario, responsable, beneficiario_y_responsable)
- `estado_validacion_renaper`: Estado de validación con RENAPER (0=no validado, 1=aceptado, 2=rechazado, 3=subsanar)

**Razón de existir**: Es la entidad central del sistema, donde se almacena toda la información específica de cada beneficiario y su proceso de validación.

**Relaciones**:
- Muchos a uno con Expediente
- Muchos a uno con Ciudadano
- Muchos a uno con EstadoLegajo
- Uno a muchos con PagoNomina

---

## Tablas de Parametría

### 3. EstadoExpediente
**Propósito**: Define los estados posibles de un expediente durante su ciclo de vida.

**Estados definidos**:
- CREADO: Expediente recién creado
- PROCESADO: Expediente procesado con ciudadanos cargados
- EN_ESPERA: En espera de asignación
- ASIGNADO: Asignado a técnico
- PROCESO_DE_CRUCE: En proceso de cruce con organismos
- CRUCE_FINALIZADO: Cruce completado
- PAGO_ABIERTO: Listo para generar pago
- PAGO_CERRADO: Pago procesado
- CONFIRMACION_DE_ENVIO: Confirmado el envío

### 4. EstadoLegajo
**Propósito**: Define los estados de los legajos individuales.

**Estados definidos**:
- DOCUMENTO_PENDIENTE: Falta documentación
- ARCHIVO_CARGADO: Documentación completa

### 5. Organismo
**Propósito**: Organismos externos con los que se realizan cruces de información.

**Organismos definidos**:
- Syntis: Sistema de cruces principales
- Salud: Ministerio de Salud
- Renaper: Registro Nacional de Personas

### 6. TipoCruce
**Propósito**: Tipos de resultado de los cruces con organismos externos.

**Tipos definidos**:
- Aprobado: Cruce exitoso
- Rechazado: Cruce con conflictos

---

## Tablas de Historial y Auditoría

### 7. ExpedienteEstadoHistorial
**Propósito**: Registra todos los cambios de estado de los expedientes para auditoría y trazabilidad.

**Campos principales**:
- `expediente`: Expediente modificado (FK)
- `estado_anterior`, `estado_nuevo`: Estados en la transición (FK a EstadoExpediente)
- `usuario`: Usuario que realizó el cambio (FK a User)
- `fecha`: Timestamp del cambio
- `observaciones`: Comentarios del cambio

### 8. HistorialValidacionTecnica
**Propósito**: Rastrea los cambios en el estado de validación técnica de los legajos.

**Campos principales**:
- `legajo`: Legajo modificado (FK a ExpedienteCiudadano)
- `estado_anterior`, `estado_nuevo`: Estados en la transición
- `usuario`: Usuario que realizó el cambio
- `motivo`: Razón del cambio

### 9. HistorialCupo
**Propósito**: Registra los cambios en el estado de cupo de los legajos.

**Campos principales**:
- `legajo`: Legajo modificado (FK)
- `estado_cupo_anterior`, `estado_cupo_nuevo`: Estados de cupo
- `es_titular_activo_anterior`, `es_titular_activo_nuevo`: Estados de titularidad
- `tipo_movimiento`: Tipo de movimiento (ALTA, BAJA, REACTIVACION, AJUSTE, SUSPENDIDO)

---

## Tablas de Gestión de Cupos

### 10. ProvinciaCupo
**Propósito**: Controla los cupos asignados y utilizados por cada provincia.

**Campos principales**:
- `provincia`: Provincia (FK a Provincia)
- `total_asignado`: Cupo total asignado a la provincia
- `usados`: Cupo actualmente utilizado

**Razón de existir**: Permite el control presupuestario y la gestión de límites por provincia.

### 11. CupoMovimiento
**Propósito**: Registra todos los movimientos que afectan el cupo provincial.

**Campos principales**:
- `provincia`: Provincia afectada (FK)
- `expediente`: Expediente relacionado (FK, opcional)
- `legajo`: Legajo específico (FK, opcional)
- `tipo`: Tipo de movimiento (ALTA, BAJA, REACTIVACION, AJUSTE, SUSPENDIDO)
- `delta`: Cambio en el cupo (+/-)
- `motivo`: Razón del movimiento
- `usuario`: Usuario que realizó el movimiento

---

## Tablas de Pagos

### 12. PagoExpediente
**Propósito**: Gestiona los expedientes de pago mensuales por provincia.

**Campos principales**:
- `provincia`: Provincia del pago (FK)
- `periodo`: Período del pago (formato YYYY-MM)
- `estado`: Estado del pago (BORRADOR, ENVIADO, PROCESADO, CERRADO)
- `archivo_envio`: Archivo enviado a SINTYS
- `archivo_respuesta`: Respuesta de SINTYS
- `total_candidatos`, `total_validados`, `total_excluidos`: Contadores de beneficiarios

**Razón de existir**: Organiza el proceso de pago mensual y mantiene el control de los archivos intercambiados con SINTYS.

### 13. PagoNomina
**Propósito**: Detalle de cada beneficiario incluido en un expediente de pago.

**Campos principales**:
- `pago`: Expediente de pago (FK a PagoExpediente)
- `legajo`: Legajo del beneficiario (FK a ExpedienteCiudadano)
- `documento`, `nombre`, `apellido`: Datos del beneficiario
- `estado`: Estado en el pago (VALIDADO, EXCLUIDO)
- `observacion`: Motivo de exclusión si aplica

---

## Tablas de Validación

### 14. AsignacionTecnico
**Propósito**: Asigna técnicos a expedientes para su revisión, permitiendo múltiples asignaciones históricas.

**Campos principales**:
- `expediente`: Expediente asignado (FK)
- `tecnico`: Usuario técnico asignado (FK a User)
- `fecha_asignacion`: Fecha de la asignación
- `activa`: Indica si la asignación está activa (permite historial)

**Mejora implementada**: Ahora soporta múltiples asignaciones por expediente manteniendo historial completo.

### 15. ValidacionTecnica
**Propósito**: Información detallada sobre la validación técnica de un legajo.

**Campos principales**:
- `legajo`: Legajo validado (FK a ExpedienteCiudadano)
- `revision_tecnico`: Estado de la revisión
- `subsanacion_motivo`: Motivo si requiere subsanación
- `subsanacion_solicitada_en`, `subsanacion_enviada_en`: Fechas del proceso de subsanación

### 16. ValidacionRenaper
**Propósito**: Gestiona la validación de identidad con RENAPER.

**Campos principales**:
- `legajo`: Legajo validado (FK)
- `estado_validacion`: Estado de la validación (0-3)
- `comentario`: Observaciones de la validación
- `archivo`: Archivo de respuesta a subsanación

### 17. CruceResultado
**Propósito**: Almacena los resultados de cruces con organismos externos.

**Campos principales**:
- `legajo`: Legajo cruzado (FK)
- `resultado_sintys`: Resultado del cruce
- `cruce_ok`: Indica si el cruce fue exitoso
- `observacion_cruce`: Detalles del resultado

### 18. CupoTitular
**Propósito**: Gestiona el estado de cupo y titularidad de los legajos.

**Campos principales**:
- `legajo`: Legajo (FK)
- `estado_cupo`: Estado respecto al cupo
- `es_titular_activo`: Indica si es titular activo

---

## Tablas de Errores y Reprocesamiento

### 19. RegistroErroneo
**Propósito**: Almacena registros que no pudieron procesarse durante la carga masiva.

**Campos principales**:
- `expediente`: Expediente donde ocurrió el error (FK)
- `fila_excel`: Número de fila en el Excel
- `datos_raw`: Datos originales en formato JSON
- `campo_error`: Campo que causó el error
- `mensaje_error`: Descripción del error
- `procesado`: Indica si fue reprocesado exitosamente

### 20. RegistroErroneoReprocesado
**Propósito**: Historial de intentos de reprocesamiento de registros erróneos.

**Campos principales**:
- `registro_erroneo`: Registro original (FK)
- `intento_numero`: Número de intento
- `resultado`: Resultado del reprocesamiento (EXITOSO, FALLIDO)
- `ciudadano_creado`, `legajo_creado`: Referencias a entidades creadas si fue exitoso
- `error_mensaje`: Mensaje de error si falló

### 21. SubsanacionRespuesta
**Propósito**: Almacena las respuestas a solicitudes de subsanación.

**Campos principales**:
- `legajo`: Legajo que responde (FK)
- `validacion_tecnica`: Validación técnica relacionada (FK)
- `archivo1`, `archivo2`, `archivo3`: Archivos de respuesta
- `comentario`: Comentarios de la respuesta
- `usuario`: Usuario que cargó la respuesta

### 22. HistorialComentarios
**Propósito**: Registra el historial completo de comentarios y subsanaciones por legajo.

**Campos principales**:
- `legajo`: Legajo al que pertenece el comentario (FK a ExpedienteCiudadano)
- `tipo_comentario`: Tipo de comentario (VALIDACION_TECNICA, SUBSANACION_MOTIVO, SUBSANACION_RESPUESTA, RENAPER_VALIDACION, OBSERVACION_GENERAL, CRUCE_SINTYS, PAGO_OBSERVACION)
- `comentario`: Texto del comentario
- `usuario`: Usuario que realizó el comentario (FK a User)
- `fecha_creacion`: Timestamp del comentario
- `archivo_adjunto`: Archivo opcional adjunto
- `estado_relacionado`: Estado del legajo al momento del comentario

**Razón de existir**: Proporciona trazabilidad completa de todos los comentarios, observaciones y subsanaciones realizadas durante el proceso de validación de un legajo. Permite auditoría completa y seguimiento histórico de decisiones técnicas.

**Relaciones**:
- Muchos a uno con ExpedienteCiudadano
- Muchos a uno con User

### 23. TipoDocumento
**Propósito**: Define los tipos de documentos que pueden ser requeridos para los legajos.

**Campos principales**:
- `nombre`: Nombre del tipo de documento
- `descripcion`: Descripción detallada del documento
- `requerido`: Indica si es obligatorio para completar el legajo
- `orden`: Orden de presentación en interfaces
- `activo`: Indica si el tipo está activo

**Razón de existir**: Normaliza y centraliza la gestión de tipos de documentos, permitiendo flexibilidad en los requerimientos documentales sin cambios de código.

### 24. DocumentoLegajo
**Propósito**: Almacena los documentos específicos asociados a cada legajo.

**Campos principales**:
- `legajo`: Legajo al que pertenece (FK a ExpedienteCiudadano)
- `tipo_documento`: Tipo de documento (FK a TipoDocumento)
- `archivo`: Archivo del documento
- `fecha_carga`: Timestamp de carga
- `usuario_carga`: Usuario que cargó el documento (FK a User)
- `observaciones`: Observaciones sobre el documento

**Razón de existir**: Reemplaza el sistema rígido de archivo1, archivo2, archivo3 por un sistema flexible que permite cualquier cantidad y tipo de documentos por legajo.

**Relaciones**:
- Muchos a uno con ExpedienteCiudadano
- Muchos a uno con TipoDocumento
- Muchos a uno con User

---

## Relaciones entre Tablas

### Relaciones Principales:
1. **Expediente → ExpedienteCiudadano**: Un expediente contiene múltiples legajos
2. **ExpedienteCiudadano → Ciudadano**: Cada legajo está asociado a un ciudadano
3. **Provincia → ProvinciaCupo**: Cada provincia tiene un cupo asignado
4. **PagoExpediente → PagoNomina**: Un expediente de pago contiene múltiples beneficiarios

### Relaciones de Auditoría:
- Todas las entidades principales tienen tablas de historial asociadas
- Los cambios de estado se registran automáticamente
- Se mantiene trazabilidad de usuarios y fechas

---

## Procesos de Negocio

### 1. Proceso de Carga de Expediente
1. Se crea un **Expediente** en estado CREADO
2. Se carga un archivo Excel masivo
3. Se procesan los registros creando **ExpedienteCiudadano**
4. Los errores se almacenan en **RegistroErroneo**
5. El expediente pasa a estado PROCESADO

### 2. Proceso de Validación Técnica
1. Se asigna un técnico mediante **AsignacionTecnico**
2. El técnico revisa cada **ExpedienteCiudadano**
3. Se actualiza el campo `revision_tecnico`
4. Si requiere subsanación, se solicita mediante **ValidacionTecnica**
5. La respuesta se almacena en **SubsanacionRespuesta**

### 3. Proceso de Cruce con Organismos
1. Se envían los datos a organismos externos (SINTYS, RENAPER)
2. Los resultados se almacenan en **CruceResultado**
3. Se actualiza el `resultado_sintys` en **ExpedienteCiudadano**
4. Se valida la identidad con RENAPER mediante **ValidacionRenaper**

### 4. Proceso de Gestión de Cupos
1. Se verifica el cupo disponible en **ProvinciaCupo**
2. Se asignan cupos a legajos elegibles
3. Los movimientos se registran en **CupoMovimiento**
4. Se actualiza el estado en **CupoTitular**

### 5. Proceso de Pago
1. Se crea un **PagoExpediente** para el período
2. Se seleccionan los legajos elegibles
3. Se genera la **PagoNomina** con los beneficiarios
4. Se envía el archivo a SINTYS
5. Se procesa la respuesta y se actualiza el estado

### 6. Proceso de Manejo de Errores
1. Los errores de carga se almacenan en **RegistroErroneo**
2. Se pueden reprocesar mediante **RegistroErroneoReprocesado**
3. Se mantiene historial de todos los intentos
4. Los registros exitosos se integran al flujo normal

### 7. Proceso de Gestión de Comentarios
1. Todos los comentarios se registran automáticamente en **HistorialComentarios**
2. Los cambios en campos de comentarios disparan signals automáticos
3. Se mantiene trazabilidad completa de quién, cuándo y qué comentó
4. Los comentarios se categorizan por tipo para facilitar consultas
5. Se puede adjuntar documentación a los comentarios
6. El historial es inmutable para garantizar auditoría

---

## Consideraciones Técnicas

### Índices Optimizados
- Todas las tablas principales tienen índices en campos de búsqueda frecuente
- Se optimizan las consultas por provincia, estado y fechas
- Los campos de auditoría tienen índices para reportes

### Integridad Referencial
- Se utilizan claves foráneas con PROTECT para evitar eliminaciones accidentales
- Los campos de usuario utilizan SET_NULL para mantener historial
- Las relaciones críticas utilizan CASCADE apropiadamente

### Escalabilidad
- El diseño permite manejar grandes volúmenes de datos
- La separación por provincia facilita el particionamiento
- Los historiales permiten auditoría completa sin afectar performance

---

## Conclusión

El diseño de la base de datos del proyecto Celíacos está optimizado para manejar el ciclo completo de gestión de beneficiarios, desde la carga inicial hasta el pago final. La estructura permite:

- **Trazabilidad completa**: Cada cambio queda registrado
- **Control de cupos**: Gestión presupuestaria por provincia  
- **Validaciones múltiples**: Técnica, documental y de organismos externos
- **Manejo de errores**: Reprocesamiento y corrección de datos
- **Escalabilidad**: Diseño preparado para grandes volúmenes
- **Auditoría**: Historial completo de todas las operaciones

Esta documentación debe actualizarse cuando se realicen cambios en el esquema de base de datos o se agreguen nuevas funcionalidades al sistema.