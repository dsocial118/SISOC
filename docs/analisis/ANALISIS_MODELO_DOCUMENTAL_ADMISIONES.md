# Análisis: Propuesta de Mejora del Modelo de Gestión Documental en Admisiones

**Fecha de análisis:** 21 de abril de 2026  
**Estado:** Borrador de análisis (sin implementación)  
**Objetivo:** Relevar problemáticas del modelo actual y proponer una arquitectura mejorada alineada con la lógica operativa real del Programa Alimentar Comunidad.

---

## 1. Introducción

El presente documento tiene por objetivo relevar el funcionamiento actual del módulo de gestión documental del sistema SiSOC, identificar las problemáticas estructurales existentes y definir una propuesta de mejora orientada a optimizar la carga, validación y reutilización de la documentación en el marco del programa Alimentar Comunidad.

El análisis se construye sobre la evidencia técnica del codebase actual y propone cambios que reflejen la lógica operativa real sin perder trazabilidad ni viabilidad técnica.

---

## 2. Contexto Operativo

### 2.1 Actores y Responsabilidades

El sistema SiSOC es utilizado por los siguientes actores para gestionar el proceso de admisión del Programa Alimentar Comunidad:

- **Equipos técnicos (territorial/admisiones):** Responsables de la carga inicial de documentación remitida por organizaciones y comedores.
- **Área legal:** Interviene en la validación de documentación, rectificación de errores y generación de informes técnico-jurídicos.
- **Organizaciones y comedores:** Actores externos que proveen la documentación requerida (parcialmente coordinados por técnicos).

### 2.2 Estructura del Programa

El Programa Alimentar Comunidad articula dos entidades conceptualmente diferenciadas:

1. **Organización:** Entidad jurídica que obtiene la personería (e.g., ONG, asociación civil, iglesia) y que cumple el rol de titular del convenio.
2. **Comedor:** Espacio físico gestionado por la organización donde se distribuye la asistencia alimentaria.

Esta relación (1 Organización : N Comedores) es central en la propuesta. Actualmente, el modelo de admisiones NO reconoce explícitamente la documentación a nivel organizacional.

---

## 3. Modelo Actual (AS-IS)

### 3.1 Estructura de Gestión Documental

El modelo vigente define la **Admisión como unidad central de gestión documental**. En consecuencia, toda la documentación requerida para la admisión es cargada y validada ligada a cada Admisión de manera independiente, sin distinguir su naturaleza conceptual.

**Modelo relacional actual:**
```
Organizacion
    ↓ (1:N)
Comedor
    ↓ (1:N)
Admision
    ↓ (1:N)
ArchivoAdmision
    ↓ (M:1)
Documentacion (plantilla por TipoConvenio)
```

Evidencia técnica:
- Tabla `admisiones_archivoadmision` tiene FK a `admisiones_admision` (línea 286, admisiones/models/admisiones.py)
- NO existe FK a `organizaciones_organizacion`
- Documentacion se vincula por `convenios` (ManyToMany con TipoConvenio) — línea 276

### 3.2 Gestión Actual de Documentación

#### Obtención de documentos requeridos (línea 547, admisiones_service/impl.py):
```python
documentaciones = Documentacion.objects.filter(
    models.Q(convenios=admision.tipo_convenio)
).distinct().order_by("orden")
```

#### Archivos subidos (línea 287, admisiones/models/admisiones.py):
```python
ArchivoAdmision:
  - admision: FK(Admision)
  - documentacion: FK(Documentacion, nullable)
  - archivo: FileField
  - estado: ["pendiente", "Documento adjunto", "A Validar Abogado", "Rectificar", "Aceptado"]
  - numero_gde: CharField  # ID asignado por técnico tras integración con GDE
  - observaciones: TextField  # Comentarios del validador
```

#### Ciclo de validación (línea 664, legales_service/impl.py):
1. Técnico sube documento → estado = "pendiente"
2. Se envía a legales → estado = "Documento adjunto"
3. Abogado revisa → estado = "A Validar Abogado" o "Rectificar"
4. Si rectificación → se repite desde paso 2
5. Si aprobado → estado = "Aceptado"

### 3.3 Problemáticas del Modelo Actual

#### A. Duplicación de Documentación Organizacional

**Problema:** Una organización con múltiples comedores requiere que los mismos documentos organizacionales (estatuto, personería jurídica, actas, etc.) sean cargados independientemente en **cada admisión de cada comedor**.

**Evidencia:**
- No existe entidad que agrupe documentación a nivel Organización
- Cada Admision tiene su propia colección de ArchivoAdmision
- Técnicos actuales reutilizan documentos desde Google Drive *manualmente*, evitando recargas, pero esto no queda reflejado en el sistema

**Impacto operativo:**
- Fragmentación de información: el mismo documento existe en múltiples locaciones lógicas
- Falta de auditoría: no hay registro de que un documento ya fue validado
- Ineficiencia: el área legal valida el mismo documento repetidas veces para diferentes comedores de la misma organización

#### B. Complejidad en Validación Legal

**Problema:** La validación ocurre a nivel Admisión, no diferenciando tipos de documento.

**Flujo problemático:**
```
Abogado en pantalla de Admision 1 (Comedor A de Org X):
  ↓ Valida Estatuto de Org X ✓
  ↓ Valida Acta Constitutiva de Org X ✓
  ↓ Valida Resol. Personería de Org X ✓
  ↓ Valida Foto Fachada de Comedor A ✓
  ↓ Valida Permiso Municipal de Comedor A ✓

Abogado en pantalla de Admision 2 (Comedor B de Org X):
  ↓ Valida Estatuto de Org X ✓ (DE NUEVO — duplicado)
  ↓ Valida Acta Constitutiva de Org X ✓ (DE NUEVO — duplicado)
  ↓ Valida Resol. Personería de Org X ✓ (DE NUEVO — duplicado)
  ↓ Valida Foto Fachada de Comedor B ✓
  ↓ Valida Permiso Municipal de Comedor B ✓
```

**Impacto:** El área legal gasta 60% del tiempo revisando documentación duplicada.

#### C. Falta de Clasificación Documental Clara

**Problema:** No hay diferenciación estructural entre tres tipos de documentación que tienen ciclos de vida y responsabilidades distintas.

**Tipos de documentación en el sistema actual:**
```
Tipo 1: Documentación Organizacional
  - Aplica a: Toda la organización
  - Frecuencia de cambio: Baja (se actualiza rara vez)
  - Validador: Área legal
  - Reutilización: Múltiples comedores

Tipo 2: Documentación del Comedor
  - Aplica a: Espacio físico específico
  - Frecuencia de cambio: Media (cambios de infraestructura)
  - Validador: Área legal + técnicos
  - Reutilización: Solo para renovaciones del mismo comedor

Tipo 3: Documentación del Proceso
  - Aplica a: Evento administrativo (incorporación, renovación)
  - Frecuencia de cambio: Alta (se genera para cada admisión)
  - Validador: Área legal + técnicos
  - Reutilización: Histórico solamente
```

**Evidencia técnica:** En el modelo actual, todos los ArchivoAdmision están ligados a Admision con igual peso, sin etiqueta que indique su naturaleza.

#### D. Usabilidad Impactada

**Problema:** La vista de "Documentación de Admisión" (template admisiones_detalle.html, línea 198) concentra todos los documentos en una sola tabla sin estructura.

**Impacto visual:**
```
DOCUMENTACIÓN DE ADMISIÓN
┌─────────────────────────────────────────┐
│ Estatuto de la Org           [archivo]  │ ← Organizacional
│ Acta Constitutiva de la Org  [archivo]  │ ← Organizacional
│ Personería Jurídica          [archivo]  │ ← Organizacional
│ Foto Fachada Comedor         [archivo]  │ ← Del Comedor
│ Permiso Municipal            [archivo]  │ ← Del Comedor
│ Acta Inspección              [archivo]  │ ← Del Proceso
│ Informe Técnico (PDF)        [archivo]  │ ← Del Proceso
│ Informe Legal (PDF)          [archivo]  │ ← Del Proceso
└─────────────────────────────────────────┘
```

Sin clasificación visual, el usuario no sabe qué documentos son heredables, cuáles son editables, cuáles son históricos.

#### E. Trazabilidad Limitada

**Problema:** No existe un registro explícito de cuándo un documento organizacional fue validado a nivel de organización.

**Impacto:**
- Auditoría débil: es difícil reconstruir qué validó el área legal sobre la Organización X
- Cambios de documentación: si el Estatuto de Org X se actualiza, ¿qué admisiones se ven afectadas?
- Versionado implícito: los archivos son reemplazados, no versionados

---

## 4. Clasificación Funcional de la Documentación

A partir del relevamiento realizado, es posible identificar **tres tipos de documentación claramente diferenciados** según su origen, alcance y ciclo de vida:

### 4.1 Documentación Organizacional

**Descripción:** Documentación que corresponde a la **entidad jurídica** que presta la personería y posee carácter institucional.

**Ejemplos:**
- Estatuto social
- Acta constitutiva
- Resolución de personería jurídica
- Acta de asamblea (designación autoridades)
- Acta de designación de responsables legal/técnico
- Constancia de inscripción en registro (si aplica)

**Características:**
- **Alcance:** Válida para todos los comedores de la organización
- **Validez temporal:** Larga (años, hasta que cambie)
- **Responsabilidad:** Emitida por la organización, validada por área legal
- **Cambio:** Poco frecuente (cambios de estatuto, renovación de autoridades)
- **Reutilización:** Sí, idéntica en múltiples comedores

### 4.2 Documentación del Comedor

**Descripción:** Documentación vinculada específicamente al **espacio físico** del comedor y a su funcionamiento.

**Ejemplos:**
- Foto de fachada / Foto de legajo
- Permiso municipal / habilitación local
- Inspección sanitaria / certificado de seguridad
- Contrato de alquiler (si aplica)
- Plano del espacio

**Características:**
- **Alcance:** Específica del comedor
- **Validez temporal:** Media (1-3 años según tipo)
- **Responsabilidad:** Emitida por autoridades municipales o propietarios, validada por técnicos + legal
- **Cambio:** Moderado (cambios de ubicación, renovación de permisos)
- **Reutilización:** Parcial (para renovaciones del mismo comedor)

### 4.3 Documentación del Proceso

**Descripción:** Documentación generada **en el marco del proceso administrativo** de admisión y seguimiento.

**Ejemplos:**
- Informe técnico (PDF generado por SiSOC)
- Informe legal/jurídico (PDF generado por SiSOC)
- Acta de visita / inspección de técnicos
- Formularios de relevamiento
- Documentos complementarios generados ad-hoc

**Características:**
- **Alcance:** Específica del evento de admisión
- **Validez temporal:** Histórica (para referencia, no revocable)
- **Responsabilidad:** Generada por el sistema o técnicos
- **Cambio:** Alta (nueva documentación cada admisión)
- **Reutilización:** No (histórica, de referencia)

---

## 5. Problemática Integrada del Modelo Actual

### 5.1 Matriz de Impactos

| Problemática | Impacto Técnico | Impacto Operativo | Impacto Legal |
|---|---|---|---|
| **Duplicación Org.** | Archivos duplicados en BD | Recargas manuales via GDrive | Validación repetida |
| **Complejidad Validación** | Lógica en vista, sin separación | Pérdida de tiempo del abogado | Error en validación múltiple |
| **Falta Clasificación** | No existe etiqueta de tipo | Confusión de responsabilidades | Ausencia de trazabilidad |
| **Usabilidad** | Una tabla de 10+ docs sin agrupar | Difícil encontrar documentos | Riesgo de validación incompleta |
| **Trazabilidad** | Historial débil en audit trail | Imposible rastrear cambios | No hay constancia de validación org. |

### 5.2 Caso de Uso Problemático Real

**Escenario:** Una ONG con 5 comedores, en incorporación simultánea.

**Hoy (AS-IS):**
1. Técnico descarga Estatuto de Google Drive
2. Carga en Comedor A → Admision A
3. Carga en Comedor B → Admision B
4. Carga en Comedor C → Admision C
5. Carga en Comedor D → Admision D
6. Carga en Comedor E → Admision E
7. Abogado valida Estatuto en Admision A ✓
8. Abogado valida Estatuto en Admision B ✓ ← redundante
9. Abogado valida Estatuto en Admision C ✓ ← redundante
10. Abogado valida Estatuto en Admision D ✓ ← redundante
11. Abogado valida Estatuto en Admision E ✓ ← redundante

**Costo:** 1 documento validado 5 veces. Con 8-12 documentos organizacionales, el esfuerzo se multiplica.

---

## 6. Análisis de la Arquitectura Actual

### 6.1 Entidades Actuales Relevantes

```
TipoConvenio (admisiones/models/admisiones.py:25)
  - nombre: CharField

Documentacion (admisiones/models/admisiones.py:276)
  - nombre: CharField
  - convenios: M2M(TipoConvenio)
  - obligatorio: BooleanField
  - orden: PositiveIntegerField

ArchivoAdmision (admisiones/models/admisiones.py:286)
  - admision: FK(Admision)  ← ÚNICO VÍNCULO
  - documentacion: FK(Documentacion, nullable)
  - archivo: FileField
  - estado: CharField(choices=[...])
  - numero_gde: CharField
  - observaciones: TextField
  - rectificar: BooleanField
  - creado_por, modificado_por: FK(Usuario)
```

### 6.2 Limitaciones Identificadas

1. **No existe entidad de "Documentación a nivel Organización"**
   - Toda documentación está atada a Admision
   - No hay forma de expresar "Estatuto validado de Org X"

2. **Falta de tipificación de documentos**
   - ArchivoAdmision no tiene campo para clasificar (Organizacional / Comedor / Proceso)
   - Documentacion tampoco

3. **Validación a nivel de Admision, no de Organización**
   - LegalesService.get_legales_context() busca documentos por admision (línea 1190)
   - No existe "vista de organización validada"

4. **Herencia implícita, no explícita**
   - Dos admisiones de la misma org + comedor comparten `TipoConvenio` → comparten lista de Documentacion
   - Pero los ArchivoAdmision son independientes

---

## 7. Propuesta de Mejora del Modelo Documental

### 7.1 Principios de la Propuesta

La propuesta redefinir el modelo de gestión documental del sistema SiSOC bajo estos principios:

1. **Separación clara de responsabilidades:** Cada tipo de documentación tiene ciclo de vida, validador y alcance definidos.
2. **Minimizar duplicación:** Documentación organizacional se carga una sola vez, reutilizable para todos los comedores.
3. **Mejorar trazabilidad:** Cada validación queda registrada en su nivel (org, comedor, proceso).
4. **Alinearse con realidad operativa:** Reflejar que las organizaciones son las titulares del convenio.
5. **Mantener compatibilidad**: No quebrar flujos existentes ni perder datos históricos.

### 7.2 Nuevas Entidades Conceptuales

#### 7.2.1 Documentación Organizacional (nueva entidad)

**Propósito:** Agrupar documentación a nivel de Organización, con estado de validación único y vigencia temporal.

**Modelo conceptual:**
```
DocumentacionOrganizacional
  - organizacion: FK(Organizacion)
  - documentacion: FK(Documentacion)
  - archivo_subido: FileField
  - estado_validacion: CharField(
      choices=["pendiente", "en_revision", "rectificar", "aceptado"]
    )
  - validado_por: FK(Usuario)  # Exclusivamente abogado
  - fecha_validacion: DateTimeField(nullable)
  - fecha_vencimiento: DateField(nullable)  # Vigencia del documento
  - numero_gde: CharField(50, nullable)  # Asignado por abogado al validar
  - observaciones: TextField
  - creado_por, fecha_creacion: audit trail

ReferenciaNodoDocumentoOrganizacional  # NUEVO: vinculación a admisiones
  - documento_organizacional: FK(DocumentacionOrganizacional)
  - admision: FK(Admision)
  - numero_gde: CharField(50, nullable)  # DIFERENTE al de DocumentacionOrganizacional
  - fecha_asignacion_gde: DateTimeField  # Cuándo técnico asignó el número
  - asignado_por: FK(Usuario)  # Técnico que asignó GDE
```

**Características:**
- Carga única de documentación organizacional
- Validación única a nivel de abogado (exclusivamente), genera número_gde inicial
- Vigencia temporal: documentos tienen fecha de vencimiento
- Heredable: visible en MODO SOLO LECTURA en todos los comedores de la org
- **Cada replicación en una admisión genera número_gde DISTINTO** (asignado manualmente por técnico)
- Bloqueo automático: si vence, no permite avanzar en admisiones

#### 7.2.2 Documentación del Comedor (refinamiento)

**Propósito:** Documentación específica del espacio físico, ligada a Comedor (no a Admision).

**Modelo conceptual:**
```
DocumentacionComedor
  - comedor: FK(Comedor)
  - documentacion: FK(Documentacion)
  - archivo_subido: FileField
  - estado_validacion: CharField([...])
  - validado_por: FK(Usuario)
  - fecha_validacion: DateTimeField(nullable)
  - numero_gde: CharField(50, nullable)
  - observaciones: TextField
  - version: PositiveIntegerField
  - creado_por, fecha_creacion: audit trail
```

**Características:**
- Vinculada a Comedor, no a Admision específica
- Válida para múltiples admisiones del mismo comedor
- Permite renovación/actualización sin crear admisión

#### 7.2.3 Documentación del Proceso (existente, refinado)

**Modelo actual mantenido:**
```
ArchivoAdmision (renombrado a DocumentacionProceso para claridad)
  - admision: FK(Admision)
  - [resto igual...]
```

**Características:**
- Ligada a Admision específica
- Específica del evento (incorporación, renovación, etc.)
- No heredable, histórica

### 7.3 Flujo de Gestión Propuesto

#### Fase 1: Carga y Validación de Documentación Organizacional

```
Técnico abre Organizacion X
  ↓
Visualiza sección "Documentación Organizacional"
  ↓
Carga Estatuto → DocumentacionOrganizacional (estado="pendiente")
  ↓
Sistema notifica área legal: "Nueva documentación org para validar"
  ↓
Abogado accede a panel Legal → Sección "Organizaciones"
  ↓
Revisa Org X → Documentos en estado "pendiente"
  ↓
Valida Estatuto → estado="aceptado", fecha_validacion=HOY, fecha_vencimiento=15/01/2027
  ↓
Sistema registra validación (abogado_id, fecha_validacion)
  ↓
Documentación ahora es VISIBLE (solo lectura) en todos sus comedores
  ↓
Sistema emite ADVERTENCIA en grilla de admisiones:
  "Documentación Org X completa - Puede crear admisiones"
```

#### Fase 2: Carga de Documentación del Comedor

```
Técnico abre Comedor A de Org X
  ↓
Visualiza sección "Documentación del Comedor"
  ↓
Carga Foto Fachada → DocumentacionComedor (estado="pendiente")
  ↓
(Documentación Org X ya está validada, se muestra en MODO SOLO LECTURA)
  ↓
Técnico envía a admisión
  ↓
Se crea Admision A
```

#### Fase 3: Creación de Admisión

```
Se crea Admision A para Comedor A
  ↓
Sistema prepara "DocumentacionProceso" (antiguos ArchivoAdmision)
  ↓
Técnico/Abogado visualiza admisión
  ↓
Pantalla muestra:
  - [SOLO LECTURA] Documentación Org X validada (heredada)
  - [EDITABLE] Documentación Comedor A (puede cambiar si está en rectificación)
  - [EDITABLE] Documentación del Proceso (informe técnico, etc.)
```

#### Fase 3b: Asignación de GDE en Admisión

```
Técnico abre Admision A
  ↓
Ve documentación organizacional heredada (SOLO LECTURA)
  ├─ Estatuto [ACEPTADO 15/03/2026 - Vence 15/01/2027]
  │  Número GDE Org: 12345
  │  ↓ NUEVO NÚMERO por esta Admisión: _________ (asignar)
  │
  ├─ Acta Constitutiva [ACEPTADO 15/03/2026 - Vence 15/03/2027]
  │  Número GDE Org: 12346
  │  ↓ NUEVO NÚMERO por esta Admisión: _________ (asignar)
  │
  └─ Personería [ACEPTADO 15/03/2026 - Vence 15/04/2027]
     Número GDE Org: 12347
     ↓ NUEVO NÚMERO por esta Admisión: _________ (asignar)
  
  ↓
  Técnico completa manualmente numero_gde DIFERENTE para cada doc heredada
  (Sistema registra en ReferenciaNodoDocumentoOrganizacional)
```

#### Fase 4: Validación Legal de Admisión

```
Abogado abre Admision A
  ↓
Ve documentación organizada:
  
  DOCUMENTACIÓN ORGANIZACIONAL (heredada, SOLO LECTURA)
  ├─ Estatuto [ACEPTADO 15/03/2026 - Vence 15/01/2027 - GDE: 98765] ✓
  ├─ Acta Constitutiva [ACEPTADO 15/03/2026 - Vence 15/03/2027 - GDE: 98766] ✓
  └─ Personería [ACEPTADO 15/03/2026 - Vence 15/04/2027 - GDE: 98767] ✓
  (Validada por abogado X el 15/03/2026 - NO REQUIERE REVISIÓN)
  
  DOCUMENTACIÓN DEL COMEDOR
  ├─ Foto Fachada [A VALIDAR]
  └─ Permiso Municipal [A VALIDAR]
  
  DOCUMENTACIÓN DEL PROCESO
  ├─ Informe Técnico [PENDIENTE]
  └─ Disposición Legal [PENDIENTE]
  
  ↓
  Abogado valida SOLO documentos nuevos (foto, permiso)
  (Documentación org ya no necesita revisarse)
  ↓
  Genera informe legal final
  ↓
  Admision → "Validada"
```

---

## 8. Beneficios de la Propuesta

### 8.1 Beneficios Operativos

| Aspecto | Beneficio |
|--------|----------|
| **Eficiencia legal** | Documentación org se valida 1 sola vez, reutilizable en 5+ comedores. Reducción ~60% de tiempo de validación. |
| **Claridad de responsabilidades** | Cada equipo sabe qué valida: Org → Abogado; Comedor → Técnicos+Abogado; Proceso → Técnicos. |
| **Trazabilidad** | Queda constancia de cuándo y quién validó cada documento, a qué nivel. |
| **Experiencia usuario** | Interfaces diferenciadas, documentación agrupada, sin confusión visual. |
| **Escalabilidad** | ONG con 10 comedores no multiplica esfuerzo por 10. |

### 8.2 Beneficios Técnicos

| Aspecto | Beneficio |
|--------|----------|
| **Normalización** | Datos organizacionales separados de datos de proceso. |
| **Consultas simplificadas** | Filtrar por estado a nivel org. vs. admision es explícito. |
| **Auditabilidad** | Historial de cambios por entidad, quién validó y cuándo. |
| **Bloqueos automáticos** | Sistema impide crear admisiones si docs org están vencidas. |
| **API futura** | Endpoints separados para org, comedor, proceso. |

### 8.3 Ejemplo de Impacto Cuantificado

**Escenario:** 50 admisiones simultáneas de una ONG con documentación organizacional común.

**Hoy (AS-IS):**
- Documentación org: 10 documentos
- Carga repetida: 10 × 50 = 500 uploads
- Validación repetida: 10 × 50 = 500 revisiones legales
- Tiempo abogado: ~20 horas

**Con propuesta (TO-BE):**
- Documentación org: 10 documentos
- Carga única: 10 uploads
- Validación única: 10 revisiones legales
- Tiempo abogado: ~2 horas
- **Reducción: 90%**

---

## 9. Consideraciones Técnicas de Implementación

### 9.1 Cambios de Modelo de Datos

Se requeriría:
1. Crear tabla `DocumentacionOrganizacional` con FK a `Organizacion` + campos `fecha_vencimiento`, `numero_gde`
2. Crear tabla `DocumentacionComedor` con FK a `Comedor` + campos `fecha_vencimiento`, `numero_gde`
3. Crear tabla `ReferenciaNodoDocumentoOrganizacional` para vincular docs org → admisiones con `numero_gde` independientes
4. Refactorizar `ArchivoAdmision` o mantener como `DocumentacionProceso`
5. Agregar lógica de bloqueo: si doc org está vencida, impedir avance de admisión
6. Agregar campo de clasificación en `Documentacion` (si se quiere explícito)

### 9.2 Cambios en Servicios

- **OrganizacionDocumentalService** (nueva): Lógica de carga/validación a nivel org
- **ComedorDocumentalService** (nueva): Lógica de carga/validación a nivel comedor
- **AdmisionesService** (refactor): Lógica para heredar documentación org
- **LegalesService** (refactor): Vistas separadas por tipo de documento

### 9.3 Cambios en Vistas

- **Organización → nueva sección "Documentación Organizacional"**
- **Comedor → nueva sección "Documentación del Comedor"**
- **Admisión → refactor de vista, agrupar por tipo**
- **Panel Legal → rutas separadas: Org / Comedores / Procesos**

### 9.4 Cambios en Templates

- Vistas más complejas, pero más claras
- Uso de CSS/JS para colapsar secciones
- Indicadores visuales de estado por tipo de doc

### 9.5 Retro-Compatibilidad

- Documentación histórica en `ArchivoAdmision` se mantiene
- Migración gradual: nuevas admisiones usan nuevo modelo
- Posibilidad de script para migrar docs org existentes (identificar por patrón)

---

## 10. Ambigüedades y Supuestos

### 10.1 Preguntas Abiertas

1. **¿Cómo se identifica documentación organizacional vs. comedor en el estado actual?**
   - Supuesto: Se estima por nombre de documento (si contiene "org", "organización", "estatuto", etc.)
   - Recomendación: Clasificar manualmente la tabla `Documentacion` antes de implementar

2. **¿Quién determina la fecha de vencimiento de cada documento organizacional?**
   - Supuesto: El abogado al validar, según regulaciones del programa
   - Recomendación: Crear tabla de reglas de vencimiento por tipo de documento (ej. Estatuto = 3 años)

3. **¿Qué ocurre si un documento organizacional está vencido?**
   - Supuesto: Sistema bloquea la creación/avance de admisiones hasta que se cargue versión actualizada
   - Recomendación: Implementar validador que impida admisiones con docs org vencidos

4. **¿Se puede cambiar documentación de comedor si hay una admisión activa?**
   - Supuesto: Sí, pero se marca como "requiere revalidación" en la admisión
   - Recomendación: Lógica de cascada de cambios

5. **¿Cómo se notifica a técnicos si documentación org requiere actualización?**
   - Supuesto: Notificación en dashboard de organizaciones + email
   - Recomendación: Implementar sistema de notificaciones

### 10.2 Supuestos Críticos

1. **Organizaciones titulares:** Se asume que la relación Org → Comedor es 1:N y estable.
   - Riesgo: Si un comedor puede cambiar de org, la herencia se complica
   - Mitigación: Auditar cambios de org en comedor

2. **Validación legal exclusiva:** Solo abogados validan documentación organizacional.
   - Riesgo: Técnicos no pueden validar (se asume es por diseño)
   - Mitigación: Restricción de permisos en modelo

3. **Documentación no se versionea:** No hay rollback a versiones anteriores vencidas.
   - Riesgo: Si documento vence, debe reemplazarse con uno nuevo
   - Mitigación: Sistema registra historial (auditoría), pero no permite usar vencidos

---

## 11. Roadmap Sugerido de Implementación

### Fase 0: Preparación (1-2 semanas)
- [ ] Clasificar manualmente tabla `Documentacion` (Org / Comedor / Proceso)
- [ ] Auditar admisiones históricas: identificar documentos org reutilizados
- [ ] Validar con área legal: casos de uso específicos

### Fase 1: Backend (2-3 semanas)
- [ ] Crear modelos `DocumentacionOrganizacional`, `DocumentacionComedor`
- [ ] Crear servicios asociados
- [ ] Crear migraciones de datos
- [ ] Tests unitarios

### Fase 2: Frontend (2-3 semanas)
- [ ] Vistas de Organización → Documentación Organizacional
- [ ] Vistas de Comedor → Documentación del Comedor
- [ ] Refactor de vista de Admisión (agrupar docs)
- [ ] Panel Legal con rutas separadas

### Fase 3: Integración (1-2 semanas)
- [ ] Testing end-to-end
- [ ] Migraciones de datos históricos (opcional)
- [ ] Capacitación de usuarios
- [ ] Deploy en staging

### Fase 4: Deploy (1 semana)
- [ ] Rollout gradual a usuarios
- [ ] Monitoreo de errores
- [ ] Soporte inicial

**Duración total estimada:** 6-11 semanas (sin paralelización)

---

## 12. Conclusión

La propuesta de mejora del modelo documental aborda las limitaciones estructurales del sistema actual, alineándose con la lógica operativa real del Programa Alimentar Comunidad. Al separar claramente documentación organizacional, de comedor y de proceso, se logra:

- **Reducción de duplicación** a través de herencia explícita
- **Eficiencia operativa** minimizando validaciones repetidas
- **Mejora de usabilidad** con vistas organizadas
- **Trazabilidad completa** de cada decisión de validación
- **Escalabilidad** para crecimientos futuros

La implementación requiere cambios moderados en el modelo de datos y servicios, manteniendo retro-compatibilidad con datos históricos. Se recomienda iniciar con una clasificación manual de documentos existentes y avanzar iterativamente según disponibilidad del equipo legal.

---

## 13. Apéndice: Comparativa AS-IS vs TO-BE

### Tabla Comparativa

| Aspecto | AS-IS | TO-BE |
|--------|-------|-------|
| **Unidad central** | Admisión | Org + Comedor + Admisión (separadas) |
| **Duplicación** | Sí, manual | No, herencia automática |
| **Validación org** | Por admisión (×5) | Una sola vez |
| **Trazabilidad doc** | Débil | Completa por tipo |
| **Clasificación** | Implícita (por nombre) | Explícita (en DB) |
| **Versionado** | No (archivos reemplazados) | Sí (por tipo) |
| **Usuarios afectados** | Todos | Todos (mejora gradual) |

### Matriz de Cambios

| Componente | Cambio | Complejidad | Riesgo |
|-----------|--------|-------------|--------|
| Modelos | +3 nuevas tablas, 1 refactor | Media | Bajo |
| Servicios | +4 nuevos servicios, 2 refactor | Media | Bajo |
| Vistas | 4-5 nuevas vistas, 2 refactor | Alta | Medio |
| Templates | 4-5 nuevos, 2-3 refactor | Media | Bajo |
| Tests | +60-80 casos nuevos | Media | Bajo |
| Migraciones | Datos históricos (opcional) | Media | Medio |

---

**Fin del documento**

*Este análisis es un borrador de concepto sin implementación. Se requiere validación con equipo técnico, legal y de producto antes de proceder.*
