# Análisis Funcional del Nuevo Módulo: Programa PAS (Prestación con Acreditación de Saberes)

## Introducción

Este documento presenta un análisis funcional del módulo propuesto para el Programa PAS en el sistema SISOC (Sistema de Información Social y Organizacional). El Programa PAS es una iniciativa que vincula prestaciones sociales mensuales con la adquisición de saberes y competencias mediante cursos. A diferencia del Programa de Prestación Mensual convencional, PAS introduce un mecanismo de acreditación basado en créditos obtenidos en cursos externos, gestionado dinámicamente mediante un sistema de puntuación variable.

El objetivo de este análisis es comprender el flujo operativo, identificar los componentes clave (nómina, cursos, créditos, validaciones), definir roles y proponer consideraciones para la integración con el ecosistema existente de SISOC.

## Descripción General del Módulo

El Programa PAS gestiona prestaciones sociales mensuales condicionadas al cumplimiento de requisitos de capacitación. Cada beneficiario debe acumular una cantidad mínima de créditos mediante la participación en cursos ofrecidos por una plataforma externa (integrada vía API). El sistema determina periódicamente (cortes mensuales) quiénes cumplen con los requisitos de permanencia y genera nóminas de pago consecuentes.

Características principales:
- **Nómina inicial**: Base de beneficiarios que integran el programa.
- **Integración con plataforma de cursos**: Consumo de datos de cursos y créditos otorgados vía API.
- **Sistema dinámico de requisitos**: ABM de créditos mínimos, puntajes por curso, y reglas de permanencia modificables.
- **Acumulación de créditos**: Tracking de créditos por beneficiario según cursos completados.
- **Cortes periódicos**: Consolidación mensual de nómina de pago basada en cumplimiento de requisitos.
- **Suspensión vs. Eliminación**: Beneficiarios que no cumplen requisitos son suspendidos pero permanecen en el sistema para reactivación.
- **Historial mensual**: Registro inmutable de nóminas de pago mensuales.
- **Auditoría completa**: Trazabilidad de cambios en requisitos, acreditaciones y decisiones de permanencia.

## Roles y Responsabilidades

Los siguientes roles interactúan en el Programa PAS:

1. **Usuario Provincial (Gestor del Programa)**:
   - Carga la nómina inicial de beneficiarios.
   - Accede a reportes de desempeño y cumplimiento de créditos.
   - Realiza consolidación manual de nómina de pago (validación final antes de generación).
   - Gestiona bajas y altas puntuales en la nómina.
   - Consulta historial de nóminas mensuales.

2. **Usuario Nacional (Administrador de Requisitos)**:
   - Define y modifica los requisitos de permanencia (créditos mínimos).
   - Mantiene el ABM de créditos: agrega cursos, modifica puntajes, actualiza reglas.
   - Comunica cambios de políticas de acreditación.
   - Accede a reportes nacionales consolidados.

3. **Sistema SISOC (Automatizado)**:
   - Consume datos de cursos y créditos desde plataforma externa (API).
   - Valida acreditaciones recibidas.
   - Calcula créditos acumulados por beneficiario.
   - Genera propuestas de nómina de pago según reglas dinámicas.
   - Ejecuta cortes mensuales automáticos.
   - Suspende/reactiva beneficiarios según cumplimiento.
   - Genera documentos de nómina (Excel, reportes, derivaciones).
   - Registra acciones para auditoría.

4. **Plataforma de Cursos Externa**:
   - Ofrece cursos y otorga créditos a beneficiarios.
   - Expone datos vía API: cursos disponibles, créditos por curso, historial de acreditaciones por persona.
   - No es gestionada por SISOC, pero integrada como fuente de verdad para acreditaciones.

5. **Beneficiario (Actor Indirecto)**:
   - Participa en cursos en plataforma externa.
   - Acumula créditos.
   - Permanece o es suspendido en el programa según desempeño.

## Componentes y Entidades Clave

### 1. Nómina Inicial
- Lista de beneficiarios elegibles para participar.
- Incluye datos básicos: DNI, nombre, contacto, grupo familiar, etc.
- Integración con ciudadanos de SISOC (reutilización de legajos cuando sea posible).

### 2. Configuración de Requisitos (ABM de Créditos)
Entidad dinámica que define:
- **Créditos Mínimos Requeridos**: Cantidad total de créditos que debe acumular un beneficiario en el período (e.g., 100 créditos/mes).
- **Catálogo de Cursos**: Cursos disponibles y créditos que otorga cada uno (sincronizado con plataforma externa).
- **Período de Evaluación**: Ventana temporal para acumular créditos (e.g., mes calendario).
- **Reglas Especiales**: Excepciones, permisos temporales, bonificaciones por modalidad de curso, etc.

Comportamiento:
- Los cambios en requisitos aplican a partir de un período específico.
- Histórico de configuraciones para auditoría.
- Versiones: Permite consultar qué requisitos regían en un período anterior.

### 3. Acumulación de Créditos por Beneficiario
- Tabla que registra: Beneficiario → Curso → Créditos Otorgados → Fecha de Acreditación.
- Sincronización periódica con API de plataforma externa.
- Cálculo acumulativo: Total de créditos al período de corte.

### 4. Propuesta de Nómina de Pago
- Resultado del cálculo automático antes del corte.
- Incluye: Beneficiarios que cumplen requisitos, beneficiarios a suspender, observaciones.
- Requiere validación/consolidación manual antes de hacerse oficial.

### 5. Nómina de Pago Consolidada (Oficial)
- Versión final después de validación provincial.
- Historial mensual inmutable.
- Base para generación de documentos de derivación, DDJJ, Excel final.

### 6. Estado de Beneficiario
Posibles estados:
- **Activo**: Cumple requisitos, incluido en nómina de pago.
- **Suspendido**: No cumplió requisitos en corte anterior, pero permanece en sistema para reactivación.
- **Inactivo**: Dado de baja voluntariamente o por decisión administrativa.
- **En Revisión**: Pendiente de validación en corte.

## Flujo de Trabajo Detallado

### Fase 1: Configuración Inicial del Programa

#### Paso 1.1: Definición de Requisitos
1. Usuario Nacional accede al ABM de Créditos.
2. Define créditos mínimos requeridos para permanencia (e.g., 100 créditos/mes).
3. Carga o sincroniza catálogo de cursos desde plataforma externa con sus valores de créditos.
4. Define período de evaluación (e.g., 1 al 30 de cada mes).
5. SISOC registra configuración como "Versión 1" con fecha de vigencia.

#### Paso 1.2: Carga de Nómina Inicial
1. Usuario Provincial carga archivo Excel con beneficiarios.
2. Estructura: DNI, Nombre, Grupo Familiar, Datos de Contacto, etc.
3. SISOC valida datos y crea/reutiliza legajos en módulo de ciudadanos.
4. Se asigna estado inicial "Activo" a todos los beneficiarios.
5. Se crea nómina de pago inicial (Período 0).

#### Paso 1.3: Activación de Sincronización
1. SISOC se conecta a API de plataforma de cursos.
2. Valida acceso y permisos.
3. Inicia sincronización periódica (e.g., diaria) para traer acreditaciones nuevas.

---

### Fase 2: Ciclo Mensual

#### Paso 2.1: Sincronización de Acreditaciones (Continuo, diario)
1. SISOC consulta API de plataforma de cursos.
2. Obtiene: Cursos completados por cada beneficiario, créditos otorgados, fechas.
3. Actualiza tabla de acumulación de créditos.
4. Registra sincronización en log de auditoría.

**Nota**: Este proceso es continuo; no espera al corte.

#### Paso 2.2: Aproximación a Corte (Días antes de fin de período)
1. Usuario Provincial puede consultar reportes preliminares:
   - Beneficiarios con créditos acumulados.
   - Proyección de cumplimiento (quiénes alcanzarán requisitos antes de corte).
   - Beneficiarios en riesgo de suspensión.

#### Paso 2.3: Corte Automático (Fecha predefinida, e.g., último día del mes a las 23:59)
1. SISOC ejecuta cálculo de nómina de pago automáticamente:
   - Para cada beneficiario: Suma créditos acumulados en el período.
   - Compara contra requisitos vigentes (versión de requisitos del período).
   - Clasifica: Cumple / No Cumple.

2. Genera **Propuesta de Nómina**:
   - Beneficiarios que cumplen (estado: "Activo" → permanece en nómina).
   - Beneficiarios que no cumplen (estado: "Activo" → cambiar a "Suspendido").
   - Motivos/Detalles por cada cambio de estado.

3. Registra propuesta con timestamp y acciones en auditoría.

#### Paso 2.4: Validación y Consolidación Manual (Usuario Provincial, dentro de 48h)
1. Usuario Provincial revisa propuesta de nómina.
2. Puede hacer ajustes puntuales (e.g., excepciones, casos especiales).
3. Valida datos antes de consolidación:
   - Verifica que créditos reportados sean correctos.
   - Revisa cualquier discrepancia con plataforma de cursos.
   - Marca beneficiarios con documentación incompleta (si aplica).

4. Consolida nómina: Propuesta pasa a estado "Nómina de Pago Consolidada".

#### Paso 2.5: Generación de Documentos
1. SISOC genera automáticamente:
   - **Nómina en Excel**: Beneficiarios activos (con monto de prestación).
   - **Reporte de Suspensiones**: Beneficiarios suspendidos, motivos, créditos faltantes.
   - **Derivación a ANSES** (u otra entidad de pago): Formato estándar con datos de pago.
   - **Justificación**: Documento que explica criterios de selección.

2. Documentos almacenados en nómina de pago consolidada.

#### Paso 2.6: Descarga y Envío
1. Usuario Provincial descarga nómina final en Excel.
2. Envío externo para procesamiento de pagos.
3. Registro de envío en auditoría.

---

### Fase 3: Gestión de Cambios en Requisitos (Ad Hoc)

#### Paso 3.1: Usuario Nacional Necesita Cambiar Requisitos
**Escenario**: Disposición nacional decide aumentar créditos mínimos de 100 a 150.

1. Usuario Nacional accede a ABM de Créditos.
2. Modifica requisito: 150 créditos mínimos.
3. Define fecha de vigencia (e.g., "A partir del 1 de junio").
4. SISOC crea nueva versión (e.g., "Versión 2").

Comportamiento:
- Beneficiarios activos no son impactados inmediatamente.
- A partir de corte de junio, se aplican nuevos requisitos.
- Beneficiarios que cumplían con 100 pero no con 150 serán suspendidos.

#### Paso 3.2: Histórico de Cambios
- SISOC mantiene registro de todas las versiones de requisitos.
- Auditoría vinculada: Quién cambió, cuándo, motivo (libre o predefinido).
- Trazabilidad para justificar cambios de estado de beneficiarios.

---

### Fase 4: Reactivación de Beneficiarios Suspendidos

#### Paso 4.1: Beneficiario Suspendido Completa Más Cursos
1. Plataforma de cursos reporta nuevas acreditaciones vía API.
2. SISOC actualiza créditos acumulados.
3. Si nuevos créditos alcanzan requisitos mínimos: Sistema marca para reactivación en próximo corte.

#### Paso 4.2: Corte Siguiente
1. SISOC recalcula nómina.
2. Beneficiario suspendido que ahora cumple pasa a "Activo".
3. Se incluye en nómina de pago siguiente.
4. Registro de reactivación en auditoría.

---

### Fase 5: Cierre de Período y Auditoría

#### Paso 5.1: Cierre en SISOC
1. Período se marca como cerrado (inmutable).
2. Nómina de pago consolidada se archieva.
3. Foto de requisitos vigentes al corte se conserva.
4. Documentos generados (Excel, derivaciones, justificaciones) vinculados de forma permanente.

#### Paso 5.2: Preparación para Período Siguiente
1. Créditos de beneficiarios se reinician a 0 (o se acumulan según política, pendiente de aclarar).
2. Nómina base para período siguiente = Beneficiarios activos del período anterior (excluye suspendidos en pago, pero mantiene registros).
3. Reanudación de sincronización con plataforma de cursos.

---

## Consideraciones Funcionales

### 1. Integración con Módulos Existentes
- **Ciudadanos**: Reutilización de legajos; evitar duplicación de datos.
- **Audittrail**: Registro integral de cambios en requisitos, acreditaciones, estados, y decisiones.
- **Admisiones**: Posible integración para ingreso inicial de beneficiarios al programa.
- **Acompañamientos**: Seguimiento de beneficiarios suspendidos para re-enganche.

### 2. Gestión Dinámica de Requisitos (ABM de Créditos)
- **Flexibilidad**: Permite ajustes frecuentes sin codificación.
- **Versionado**: Histórico de requisitos para trazabilidad.
- **Aplicación temporal**: Cambios pueden ser efectivos en períodos específicos (no inmediatos).
- **Comunicación**: Usuario Nacional debe poder notificar cambios a provincias.

### 3. Sincronización con Plataforma Externa
- **Confiabilidad**: Mecanismo de reintentos en caso de fallo de API.
- **Consistencia**: Validación de datos recibidos; alertas en caso de discrepancias.
- **Latencia**: Sincronización diaria es suficiente o se requiere en tiempo real (pendiente aclarar).
- **Seguridad**: Autenticación segura con API; cifrado de datos en tránsito.

### 4. Estados y Transiciones
Máquina de estados simplificada:
```
Activo → (No cumple requisitos en corte) → Suspendido
Suspendido → (Cumple requisitos nuevamente) → Activo
Activo/Suspendido → (Baja manual) → Inactivo
```

### 5. Acumulación de Créditos
- **Pendiente aclarar**: ¿Los créditos se reinician cada mes o son acumulativos en el año?
- **Cursos parciales**: ¿Qué sucede si el beneficiario completa un curso después del corte?
- **Duplicación**: ¿Un mismo curso puede completarse múltiples veces? ¿Otorga créditos múltiples?

### 6. Suspensión vs. Eliminación
- **Suspensión**: Beneficiario no recibe pago, pero se mantiene en sistema para reactivación.
- **Auditoría**: Histórico de suspensión/reactivación para análisis.
- **Comunicación**: ¿Sistema notifica al beneficiario de su suspensión?

### 7. Documentos y Reportes
- **Nómina de Pago**: Beneficiarios activos, montos, datos bancarios.
- **Reporte de Suspensiones**: Beneficiarios suspendidos, créditos acumulados vs. requeridos, motivo.
- **Justificación**: Documento que explica criterios para auditoría/comunicación externa.
- **Histórico Mensual**: Consulta de nóminas pasadas, razones de cambios.

### 8. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| API de plataforma de cursos no disponible | Desincronización de créditos | Reintentos, alertas, modo degradado |
| Discrepancia entre créditos reportados y reales | Inclusion/exclusión incorrecta de beneficiarios | Validación de datos, auditoría de sincronizaciones |
| Cambio de requisitos afecta inadecuadamente | Suspensiones injustas | Versionado, período de vigencia, comunicación clara |
| Volumen alto de beneficiarios | Rendimiento en corte | Optimización de cálculos, procesamiento asincrónico |
| Datos incompletos en nómina inicial | Integración fallida con ciudadanos | Validación previa, reporte de errores, corrección manual |

### 9. Escalabilidad y Rendimiento
- **Volumen**: Estimación de beneficiarios y cursos (pendiente).
- **Frecuencia**: Cortes mensuales (bajo impacto).
- **Sincronización**: Diaria con API (requiere caching/optimización).

### 10. Políticas Pendientes de Aclaración
- Cantidad exacta de créditos mínimos requeridos (inicialmente).
- Créditos otorgados por cada curso.
- ¿Acumulación anual o por período?
- ¿Cursos pueden repetirse?
- Período de evaluación (mes calendario, móvil, otro).
- Notificaciones a beneficiarios sobre estado/suspensión.
- Proceso de apelación o revisión de suspensiones.

## Arquitectura de Datos (Bosquejo)

### Tablas/Entidades Principales

1. **program_pas_requirements** (ABM de Créditos)
   - id, version, credits_minimum, period_start, period_end, created_by, created_at, status

2. **program_pas_course_catalog**
   - id, course_id (de plataforma externa), course_name, credits_value, version, active

3. **program_pas_beneficiary** (Nómina)
   - id, citizen_id (relación a módulo ciudadanos), status (Activo/Suspendido/Inactivo), joined_date, suspended_date

4. **program_pas_credits_accrual**
   - id, beneficiary_id, course_id, credits_earned, accrual_date, sync_timestamp

5. **program_pas_payroll** (Nómina de Pago)
   - id, period, version (Propuesta/Consolidada), beneficiaries_list, generated_date, consolidated_date, status

6. **program_pas_payroll_audit**
   - id, payroll_id, action (Propuesta/Consolidada/Generada), actor, timestamp, details

---

## Conclusiones y Próximos Pasos

El Programa PAS introduce un mecanismo innovador de condicionamiento de prestaciones a la acreditación de saberes. Su implementación requiere:

1. **Clarificación de Políticas**:
   - Definir créditos mínimos iniciales.
   - Especificar créditos por curso.
   - Resolver acumulación (período vs. anual).

2. **Integración Técnica**:
   - Conectar con API de plataforma de cursos.
   - Diseñar ABM de créditos como módulo independiente pero integrado.
   - Validar integración con módulo de ciudadanos.

3. **Prototipo Funcional**:
   - Mockup de flujo de corte automático.
   - Plantilla de reporte de suspensiones.
   - Diseño de dashboard de requisitos para Usuario Nacional.

4. **Documentación de Procedimientos**:
   - Manual para Usuario Provincial (carga nómina, consolidación).
   - Manual para Usuario Nacional (gestión de requisitos).
   - Procedimiento de escalación ante errores o excepciones.

5. **Testing**:
   - Casos de uso: Beneficiario activo → suspendido → reactivado.
   - Casos de borde: Sincronización fallida, cambio de requisitos en mitad de período.
   - Carga: Volúmenes realistas de beneficiarios y cursos.

Este análisis establece la base para diseño técnico y desarrollo. Se recomienda iterar con usuarios provinciales y nacionales para refinar políticas, especialmente en decisiones pendientes sobre acumulación y requisitos.
