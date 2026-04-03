# Guía de Desarrollo — Módulo VAT (Marketplace INET/VAT)

> Documento vivo. Se actualiza a medida que se recibe documentación del requerimiento.
> Última actualización: junio 2025.

---

## Tabla de Contenidos

1. [Objetivo del Módulo](#1-objetivo-del-módulo)
2. [Modelo de Datos — DER v4](#2-modelo-de-datos--der-v4)
3. [Descripción de Entidades](#3-descripción-de-entidades)
4. [Roles y Permisos](#4-roles-y-permisos)
5. [Reglas de Negocio](#5-reglas-de-negocio)
6. [Voucher y Validación de Inscripción](#6-voucher-y-validación-de-inscripción)
7. [Flujos Funcionales](#7-flujos-funcionales)
8. [Estado Actual de Implementación](#8-estado-actual-de-implementación)
9. [Gap Analysis — DER v4 vs Código Actual](#9-gap-analysis--der-v4-vs-código-actual)
10. [Plan de Implementación](#10-plan-de-implementación)
11. [Decisiones Técnicas](#11-decisiones-técnicas)
12. [Endpoints API](#12-endpoints-api)
13. [Changelog del Documento](#13-changelog-del-documento)

---

## 1. Objetivo del Módulo

Marketplace de formación profesional que unifica oferta de INET y VAT.
Permite a instituciones publicar oferta formativa, gestionar comisiones, inscripciones,
asistencia y evaluaciones. Incluye un front público para búsqueda de oferta y un
backoffice para administración.

---

## 2. Modelo de Datos — DER v4

### 2.1 Matriz Maestra

Fuente: "Matriz Maestra Final — Marketplace INET / VAT" (DER v4).
Ajuste recomendado: agregar `programa_origen_id` en `oferta_institucional`.

#### Maestras / Institucionales

| Entidad | PK | FKs | Atributos clave |
|---|---|---|---|
| organismo | organismo_id | — | nombre, sigla, tipo, activo → **Resuelto: `organizaciones.Organizacion`** |
| programa_origen | programa_origen_id | organismo_id → organismo | nombre, descripcion, activo → **Resuelto: `core.Programa` (extender)** |
| modalidad_institucional | modalidad_institucional_id | — | nombre, descripcion, activo |
| institucion | institucion_id | modalidad_institucional_id → modalidad_institucional | nombre, tipo_gestion, clase_institucion, situacion, fecha_alta, activo → **Resuelto: extender `VAT.Centro`** |
| institucion_identificador_hist | ident_hist_id | institucion_id → institucion | tipo_identificador, valor_identificador, rol_institucional, vigencia_desde/hasta, motivo, es_actual |
| institucion_contacto | contacto_id | institucion_id → institucion | email, telefono, sitio_web, observaciones, es_principal, vigencia_desde/hasta |
| autoridad_institucional | autoridad_id | institucion_id → institucion | persona_nombre, dni, cargo, email, telefono, vigencia_desde/hasta, es_actual |
| ubicacion | ubicacion_id | — | nombre_referencia, tipo_ubicacion, provincia, municipio, localidad, domicilio, latitud, longitud, activo |
| institucion_ubicacion | institucion_ubicacion_id | institucion_id → institucion, ubicacion_id → ubicacion | rol_ubicacion, vigencia_desde/hasta, es_principal, observaciones |

#### Académicas / Catálogos

| Entidad | PK | FKs | Atributos clave |
|---|---|---|---|
| sector | sector_id | — | nombre, descripcion |
| subsector | subsector_id | sector_id → sector | nombre, descripcion |
| titulo_referencia | titulo_referencia_id | sector_id → sector, subsector_id → subsector | codigo_referencia, nombre, descripcion, activo |
| modalidad_cursada | modalidad_cursada_id | — | nombre, descripcion, activo |
| plan_version_curricular | plan_version_id | titulo_referencia_id → titulo_referencia, modalidad_cursada_id → modalidad_cursada | normativa, version, horas_reloj, nivel_requerido, nivel_certifica, frecuencia, activo |

#### Oferta y Operación

| Entidad | PK | FKs | Atributos clave |
|---|---|---|---|
| oferta_institucional | oferta_institucional_id | institucion_id → institucion, plan_version_id → plan_version_curricular, programa_origen_id → programa_origen | nombre_local, ciclo_lectivo, plan_externo_id, estado_oferta, aprob_jurisdiccion, aprob_inet, fecha_publicacion |
| comision | comision_id | oferta_institucional_id → oferta_institucional, institucion_ubicacion_id → institucion_ubicacion | codigo_comision, nombre, fecha_inicio, fecha_fin, cupo, estado |
| comision_horario | comision_horario_id | comision_id → comision | dia_semana, hora_desde, hora_hasta, aula_espacio, vigente |
| encuentro | encuentro_id | comision_id → comision, comision_horario_id → comision_horario | fecha, hora_desde, hora_hasta, estado, observaciones |

#### Personas y Trayectoria

| Entidad | PK | FKs | Atributos clave |
|---|---|---|---|
| persona | persona_id | — | dni, nombre, apellido, fecha_nacimiento, genero, email, telefono, nivel_estudio_maximo, domicilio_dni, domicilio_actual, domicilio_actual_confirmado, origen_validacion |
| inscripcion | inscripcion_id | persona_id → persona, comision_id → comision, programa_origen_id → programa_origen | fecha_inscripcion, estado, origen_canal, fecha_validacion_presencial, observaciones |
| asistencia | asistencia_id | inscripcion_id → inscripcion, encuentro_id → encuentro | presente, fecha_registro, observaciones |
| evaluacion | evaluacion_id | comision_id → comision | tipo, nombre, fecha, es_final |
| resultado_evaluacion | resultado_evaluacion_id | evaluacion_id → evaluacion, inscripcion_id → inscripcion | aprobo, fecha_registro |

### 2.2 Visibilidad Front vs Backoffice

Campos visibles en front público (según matriz):
- institucion.nombre
- ubicacion: provincia, municipio, localidad
- oferta_institucional: nombre_local, ciclo_lectivo, estado_oferta
- plan_version_curricular: horas_reloj (vía oferta/comisión)
- comision: nombre, fecha_inicio, fecha_fin, cupo
- comision_horario: dia_semana, hora_desde, hora_hasta, aula_espacio
- persona: dni, nombre, apellido, email, telefono (parcial, autogestión)
- inscripcion: fecha_inscripcion, estado (parcial, seguimiento)

Todo lo demás es solo backoffice.

---

## 3. Descripción de Entidades

### 3.1 Maestras / Institucionales

- **organismo**: Entidad macro rectora. Identifica la institución superior bajo la cual existen programas de origen.
- **programa_origen**: Programa específico (ej. INET, VAT) desde el cual se oferta la formación. Conserva trazabilidad del origen.
- **modalidad_institucional**: Clasifica el tipo/modalidad institucional. Tipifica instituciones dentro del modelo organizacional.
- **institucion**: Entidad central oferente. Publica oferta formativa, tiene autoridades, contactos, ubicaciones y comisiones.
- **institucion_identificador_hist**: Historial de identificadores (códigos, roles institucionales, vigencias). Evita perder trazabilidad cuando cambian.
- **institucion_contacto**: Datos de contacto institucional (email, teléfono, web). Determina cuál es el contacto principal.
- **autoridad_institucional**: Autoridades asociadas a una institución. Registra cargo, vigencia y datos de contacto.
- **ubicacion**: Localización física/territorial. Provincia, municipio, localidad, domicilio y coordenadas.
- **institucion_ubicacion**: Relación institución↔ubicación. Permite múltiples sedes con roles diferenciados y vigencia.

### 3.2 Académicas / Catálogos

- **sector**: Gran campo o sector de formación. Organiza la oferta en grandes áreas temáticas.
- **subsector**: Desagregación de un sector. Mayor precisión en la organización académica/técnica.
- **titulo_referencia**: Título o referencia formativa. Ancla conceptual y normativa de la formación.
- **modalidad_cursada**: Modalidad pedagógica (presencial, virtual, mixta). Normaliza cómo se dicta la formación.
- **plan_version_curricular**: Versión concreta de un plan curricular. Conserva normativa, versión, carga horaria, requisitos.

### 3.3 Oferta y Operación

- **oferta_institucional**: Oferta concreta publicada. Lo que el usuario ve como curso en el marketplace. Vincula institución + plan + ciclo + estado + programa_origen.
- **comision**: Ejecución concreta de una oferta. Maneja cupos, fechas, estado. Instancia real donde las personas se inscriben.
- **comision_horario**: Días y horarios de una comisión. Estructura la agenda regular de cursada.
- **encuentro**: Clase o encuentro puntual. Registra fechas efectivas, horarios reales, estado. Vincula asistencia.

### 3.4 Personas y Trayectoria

- **persona**: Persona que interactúa como aspirante/inscripto. Centraliza identidad, contacto, validación y datos personales.
- **inscripcion**: Acto de inscripción a una comisión. Reemplaza la idea de "solicitud". Registra estado, fecha, canal, validación presencial, programa de origen.
- **asistencia**: Asistencia de una persona inscripta a un encuentro. Controla presencia y trazabilidad.
- **evaluacion**: Instancia evaluativa dentro de una comisión. Exámenes, trabajos, parciales o finales.
- **resultado_evaluacion**: Resultado de una evaluación para una inscripción. Registra aprobación y trazabilidad.

---

## 4. Roles y Permisos

### 4.1 Roles identificados en código actual

| Rol | Permission code | Alcance |
|---|---|---|
| Superuser | (Django built-in) | Acceso total |
| CFPINET | `auth.role_vat_sse` | Ve todos los centros, puede crear centros y actividades |
| CFPJuridicccion | `auth.role_provincia_vat` | Crea y edita centros dentro de su jurisdicción, y administra planes curriculares provinciales |
| CFP | `auth.role_referentecentrovat` | Ve solo sus centros asignados y gestiona cursos, comisiones, horarios, asistencia e inscripciones dentro de esos centros |

### 4.2 Roles pendientes de definición

> ⚠️ Pendiente: documentación de roles del DER v4 / Marketplace.

- Administrador de organismo
- Administrador de institución
- Referente de comisión / docente
- Persona / aspirante (autogestión front)
- Aprobador jurisdiccional
- Aprobador INET

---

## 5. Reglas de Negocio

### 5.1 Reglas implementadas actualmente

**Centros**
- Un centro puede estar activo o inactivo.
- Solo el referente asignado, superuser o rol CFPINET pueden editar/eliminar un centro.
- Referente solo ve sus centros; SSE ve todos.

**Actividades (ActividadCentro)**
- Estados: planificada → en_curso → finalizada.
- Fecha fin no puede ser anterior a fecha inicio.
- Al crear una actividad con fechas y días, se generan encuentros automáticamente.
- Al editar, se regeneran encuentros (preservando los que ya tienen asistencia).

**Participantes**
- Estados: inscrito → dado_baja | lista_espera → inscrito.
- Validación de cupo: si cupo lleno → lista de espera (con confirmación).
- Validación de sexo: si la actividad restringe sexo, se valida.
- Al dar de baja, se promueve automáticamente el siguiente de lista de espera.
- Unique: un ciudadano no puede estar inscrito dos veces en la misma actividad.
- Todo cambio de estado queda en historial con usuario y timestamp.

**Encuentros**
- Se generan automáticamente según días y rango de fechas de la actividad.
- Estados: programado → realizado | cancelado.
- Unique: una actividad no puede tener dos encuentros en la misma fecha.

**Asistencia**
- Estados: presente / ausente / justificado.
- Unique: un participante tiene una sola asistencia por encuentro.
- Al registrar asistencia, el encuentro pasa a "realizado".

**Beneficiarios / Responsables**
- Búsqueda de beneficiario por CUIL contra padrón externo.
- Consulta a RENAPER para obtener datos personales (beneficiario y responsable).
- Cache de datos RENAPER en sesión y en modelo BeneficiariosResponsablesRenaper.
- Un beneficiario tiene un responsable obligatorio.
- Relación M2M beneficiario↔responsable con vínculo parental.

### 5.2 Reglas pendientes de definición (DER v4)

> ⚠️ Pendiente: documentación de reglas de negocio del marketplace.

- Estados de oferta_institucional y transiciones.
- Flujo de aprobación (jurisdicción + INET).
- Reglas de inscripción (canal, validación presencial).
- Reglas de evaluación y aprobación.
- Reglas de vigencia en contactos, ubicaciones, autoridades.
- Reglas de publicación en front.

---

## 6. Voucher y Validación de Inscripción

### 6.1 Sistema de Voucher (Bono de consumo)

#### Concepto

Cada ciudadano/persona tiene un **saldo de voucher** que puede consumir al inscribirse
en actividades/comisiones que tengan costo. El saldo se gestiona desde el legajo del
ciudadano y se configura a nivel de programa.

#### Configuración por programa

Cada `programa_origen` define la política de voucher:

| Atributo | Tipo | Descripción |
|---|---|---|
| voucher_habilitado | BOOLEAN | Si el programa usa sistema de voucher |
| monto_voucher | DECIMAL | Monto asignado por período |
| periodo_voucher | VARCHAR | Frecuencia de recarga (mensual, etc.) |
| tipo_carga | VARCHAR | `automatica` o `manual` |
| tipo_inscripcion | VARCHAR | `unica` o `multiple` |

- **Carga automática**: el sistema acredita el monto configurado al inicio de cada período (ej. mensual) a todos los ciudadanos activos del programa.
- **Carga manual**: un operador asigna/ajusta el saldo desde el backoffice.
- **Inscripción única**: el ciudadano solo puede tener **una inscripción activa** (inscrito / en curso) a la vez dentro del programa. Una vez que la actividad/comisión finaliza, puede inscribirse a otra.
- **Inscripción múltiple**: el ciudadano puede tener **múltiples inscripciones simultáneas** dentro del programa sin restricción.

#### Configuración por actividad/comisión

Al crear o editar una actividad/comisión se define:

| Atributo | Tipo | Descripción |
|---|---|---|
| requiere_voucher | BOOLEAN | Si la actividad tiene costo y descuenta voucher |
| monto_actividad | DECIMAL | Monto que se descuenta del saldo al inscribirse |

- Si `requiere_voucher = False` → actividad gratuita, no descuenta nada.
- Si `requiere_voucher = True` → al inscribirse se valida saldo y se descuenta `monto_actividad`.

#### Legajo del ciudadano — Sección Voucher

En el legajo/perfil del ciudadano se agrega una sección de voucher con:

| Dato | Descripción |
|---|---|
| Saldo actual | Monto disponible para consumir |
| Historial de movimientos | Lista de créditos y débitos con fecha, concepto, monto |
| Programa asociado | De qué programa viene el saldo |

#### Entidades propuestas

**voucher_config_programa** (configuración por programa)

| Atributo | Tipo | Oblig. | Descripción |
|---|---|---|---|
| voucher_config_id | BIGINT PK | Sí | Clave primaria |
| programa_origen_id | BIGINT FK | Sí | FK a programa_origen |
| voucher_habilitado | BOOLEAN | Sí | Si el programa usa voucher |
| monto_voucher | DECIMAL(10,2) | Sí | Monto por período |
| periodo_voucher | VARCHAR(50) | Sí | Frecuencia: mensual, bimestral, etc. |
| tipo_carga | VARCHAR(20) | Sí | `automatica` / `manual` |
| tipo_inscripcion | VARCHAR(20) | Sí | `unica` / `multiple` |
| activo | BOOLEAN | Sí | Si la config está vigente |

**voucher_saldo** (saldo por ciudadano por programa)

| Atributo | Tipo | Oblig. | Descripción |
|---|---|---|---|
| voucher_saldo_id | BIGINT PK | Sí | Clave primaria |
| persona_id | BIGINT FK | Sí | FK a persona/ciudadano |
| programa_origen_id | BIGINT FK | Sí | FK a programa_origen |
| saldo_actual | DECIMAL(10,2) | Sí | Saldo disponible |
| fecha_ultima_recarga | DATETIME | No | Última recarga automática o manual |

**voucher_movimiento** (historial de movimientos)

| Atributo | Tipo | Oblig. | Descripción |
|---|---|---|---|
| movimiento_id | BIGINT PK | Sí | Clave primaria |
| voucher_saldo_id | BIGINT FK | Sí | FK a voucher_saldo |
| tipo_movimiento | VARCHAR(20) | Sí | `credito` / `debito` |
| monto | DECIMAL(10,2) | Sí | Monto del movimiento |
| saldo_anterior | DECIMAL(10,2) | Sí | Saldo antes del movimiento |
| saldo_posterior | DECIMAL(10,2) | Sí | Saldo después del movimiento |
| concepto | VARCHAR(200) | Sí | Descripción (ej. "Recarga mensual", "Inscripción a Taller X") |
| inscripcion_id | BIGINT FK | No | FK a inscripcion (si es débito por inscripción) |
| usuario_id | BIGINT FK | No | FK a User (quién hizo la operación, null si automática) |
| fecha | DATETIME | Sí | Fecha/hora del movimiento |

#### Reglas de negocio — Voucher

1. **Inscripción a actividad paga**: al inscribirse, el sistema verifica que `saldo_actual >= monto_actividad`. Si no alcanza → rechaza inscripción con mensaje de saldo insuficiente.
2. **Débito**: al confirmar inscripción se crea un movimiento tipo `debito` y se actualiza `saldo_actual`.
3. **Crédito automático**: si `tipo_carga = automatica`, un proceso periódico (cron/celery) acredita `monto_voucher` a todos los ciudadanos activos del programa al inicio de cada `periodo_voucher`.
4. **Crédito manual**: un operador puede acreditar/ajustar saldo desde el backoffice. Queda registrado con `usuario_id`.
5. **Baja de inscripción**: al dar de baja una inscripción paga → se reintegra el monto como crédito (decisión pendiente: ¿siempre o con condiciones?).
6. **Actividades gratuitas**: `requiere_voucher = False` → no se valida ni descuenta nada.
7. **Convivencia**: en un mismo programa pueden coexistir actividades gratuitas y pagas.

#### Reglas de negocio — Tipo de inscripción por programa

1. Si `tipo_inscripcion = unica` → al inscribir, el sistema verifica si el ciudadano ya tiene una inscripción activa (estado `inscrito` o en curso) en **cualquier** comisión/actividad del mismo programa.
2. Si ya tiene una activa → rechaza inscripción con mensaje "Ya tiene una inscripción activa en este programa. Debe finalizar la actual para inscribirse a otra".
3. Inscripciones en estado `finalizada`, `dado_baja` o `lista_espera` **no bloquean** una nueva inscripción.
4. Si `tipo_inscripcion = multiple` → no se aplica restricción, puede inscribirse a tantas como quiera (sujeto a cupo, voucher, padrón, etc.).

### 6.2 Validación de Inscripción contra Padrón

#### Concepto

Al configurar una actividad/comisión se puede definir que **requiere validación**.
Esto significa que al momento de inscribir a un ciudadano, el sistema busca en una
**tabla de padrón por programa** para verificar si el ciudadano está habilitado.

#### Configuración por actividad/comisión

| Atributo | Tipo | Descripción |
|---|---|---|
| requiere_validacion_padron | BOOLEAN | Si la inscripción requiere estar en el padrón del programa |

#### Tabla de padrón por programa

**padron_programa** (lista blanca por programa)

| Atributo | Tipo | Oblig. | Descripción |
|---|---|---|---|
| padron_id | BIGINT PK | Sí | Clave primaria |
| programa_origen_id | BIGINT FK | Sí | FK a programa_origen |
| dni | VARCHAR(20) | Sí | DNI del ciudadano habilitado |
| cuil | VARCHAR(20) | No | CUIL (opcional, para cruce) |
| nombre | VARCHAR(150) | No | Nombre (informativo) |
| apellido | VARCHAR(150) | No | Apellido (informativo) |
| activo | BOOLEAN | Sí | Si el registro está vigente |
| fecha_alta | DATE | Sí | Cuándo se agregó al padrón |
| fecha_baja | DATE | No | Cuándo se dio de baja (si aplica) |

> Nota: esta tabla puede ser cargada por importación masiva (CSV/Excel) o por operador.
> Es una tabla por programa, no por actividad. La actividad solo indica si requiere validación.

#### Reglas de negocio — Validación de inscripción

1. Si `requiere_validacion_padron = True` → al inscribir, el sistema busca al ciudadano (por DNI) en `padron_programa` filtrando por el `programa_origen` de la actividad/comisión.
2. Si el ciudadano **no está** en el padrón o `activo = False` → rechaza inscripción con mensaje "El ciudadano no está habilitado para este programa".
3. Si el ciudadano **está** y `activo = True` → permite la inscripción normalmente.
4. Si `requiere_validacion_padron = False` → no se valida, cualquiera puede inscribirse.

### 6.3 Combinación de ambas validaciones

Ambos flags son independientes y combinables:

| requiere_voucher | requiere_validacion_padron | Comportamiento |
|---|---|---|
| ❌ | ❌ | Inscripción libre y gratuita |
| ✅ | ❌ | Valida saldo, descuenta voucher |
| ❌ | ✅ | Valida padrón, sin costo |
| ✅ | ✅ | Valida padrón + valida saldo + descuenta voucher |

Orden de validación en inscripción:
1. Validar cupo (existente)
2. Validar sexo (existente)
3. Validar inscripción única (si `tipo_inscripcion = unica` en el programa)
4. Validar padrón del programa (si `requiere_validacion_padron`)
5. Validar saldo voucher (si `requiere_voucher`)
6. Crear inscripción + débito de voucher (si aplica)

---

## 7. Flujos Funcionales

### 7.1 Flujos implementados

**Flujo Centro → Actividad → Participante → Asistencia**
1. SSE crea centro con datos de ubicación, contacto y referente.
2. SSE o referente crea actividad en el centro (categoría, horarios, cupo, fechas).
3. Sistema genera encuentros automáticamente.
4. Se inscriben participantes (ciudadanos) validando cupo y sexo.
5. En cada encuentro se registra asistencia bulk.

**Flujo Beneficiarios**
1. Operador busca CUIL en padrón.
2. Si existe, consulta RENAPER para datos personales.
3. Operador busca/crea responsable (también vía RENAPER).
4. Se crea beneficiario vinculado al responsable.

### 7.2 Flujo de inscripción con Voucher y Validación

```
Ciudadano quiere inscribirse a actividad/comisión
  │
  ├─ 1. ¿Hay cupo? ──── No → Lista de espera / Rechazar
  │
  ├─ 2. ¿Restricción de sexo? ──── No cumple → Rechazar
  │
  ├─ 3. ¿tipo_inscripcion = unica? (config programa)
  │     └─ Sí → ¿Tiene inscripción activa en el programa?
  │              └─ Sí → Rechazar: "Ya tiene inscripción activa"
  │
  ├─ 4. ¿requiere_validacion_padron?
  │     └─ Sí → Buscar DNI en padron_programa del programa
  │              └─ No encontrado / inactivo → Rechazar: "No habilitado"
  │
  ├─ 5. ¿requiere_voucher?
  │     └─ Sí → Verificar saldo_actual >= monto_actividad
  │              └─ Saldo insuficiente → Rechazar: "Saldo insuficiente"
  │
  ├─ 6. Crear inscripción (estado: inscrito)
  │
  └─ 7. Si requiere_voucher → Crear movimiento débito + actualizar saldo
```

### 7.3 Flujo de recarga automática de Voucher

```
Proceso periódico (celery beat / cron)
  │
  ├─ Para cada programa con voucher_habilitado y tipo_carga = automatica
  │     │
  │     ├─ Obtener ciudadanos activos del programa
  │     │
  │     ├─ Para cada ciudadano:
  │     │     ├─ Obtener o crear voucher_saldo
  │     │     ├─ Crear movimiento tipo credito por monto_voucher
  │     │     └─ Actualizar saldo_actual
  │     │
  │     └─ Registrar fecha_ultima_recarga
```

### 7.4 Flujos pendientes de definición (DER v4)

> ⚠️ Pendiente: documentación de flujos del marketplace.

- Flujo de publicación de oferta (institución → aprobación → publicación).
- Flujo de inscripción desde front (persona → búsqueda → inscripción → validación).
- Flujo de seguimiento académico (asistencia + evaluación → resultado).
- Flujo de autogestión de persona.

---

## 8. Estado Actual de Implementación

### 7.1 Modelos existentes (VAT/models.py)

| Modelo | Soft Delete | Descripción |
|---|---|---|
| Centro | ✅ | Centro VAT con ubicación, referente, organización, contacto |
| Categoria | ✅ | Categoría de actividades |
| Actividad | ✅ | Actividad genérica (nombre + categoría) |
| ActividadCentro | ✅ | Instancia de actividad en un centro (días, horarios, cupo, estado, fechas) |
| ParticipanteActividad | ✅ | Inscripción de Ciudadano a ActividadCentro |
| ParticipanteActividadHistorial | ❌ | Auditoría de cambios de estado |
| Encuentro | ❌ | Encuentro programado por actividad |
| Asistencia | ❌ | Registro de asistencia por encuentro |
| Responsable | ✅ | Adulto responsable de beneficiarios |
| Beneficiario | ✅ | Menor/beneficiario vinculado a responsable |
| BeneficiarioResponsable | ✅ | Tabla intermedia beneficiario↔responsable |
| PadronBeneficiarios | ❌ | Tabla no gestionada (padrón externo, read-only) |
| BeneficiariosResponsablesRenaper | ❌ | Cache de datos RENAPER |

### 7.2 Servicios existentes (VAT/services/)

| Servicio | Ubicación | Función |
|---|---|---|
| ParticipanteService | services/participante/ | Inscripción, baja, promoción lista espera, búsqueda ciudadanos |
| EncuentroService | services/encuentro_service/ | Generación/regeneración de encuentros |
| AsistenciaService | services/encuentro_service/ | Registro bulk de asistencia |
| centro_service | services/centro_service/ | Solo `puede_operar()` |
| actividad_service | services/actividad_service/ | Solo `actividades_disponibles_para_centro()` |
| beneficiarios_service | services/beneficiarios_service/ | CRUD beneficiarios, búsqueda RENAPER, filtros |
| consulta_renaper | services/consulta_renaper/ | Cliente API RENAPER |
| form_service | services/form_service/ | Helpers de formularios (ubicación, readonly) |
| centro_filter_config | services/centro_filter_config/ | Config filtros avanzados centros |
| beneficiarios_filter_config | services/beneficiarios_filter_config/ | Config filtros avanzados beneficiarios |
| responsables_filter_config | services/responsables_filter_config/ | Config filtros avanzados responsables |

### 7.3 Vistas existentes

| Vista | Tipo | URL base |
|---|---|---|
| CentroListView | ListView + AJAX | /vat/centros/ |
| CentroDetailView | DetailView | /vat/centros/<pk>/ |
| CentroCreateView | CreateView | /vat/centros/nuevo/ |
| CentroUpdateView | UpdateView | /vat/centros/<pk>/editar/ |
| CentroDeleteView | DeleteView (soft) | /vat/centros/<pk>/eliminar/ |
| ActividadCentroListView | ListView | /vat/actividades/ |
| ActividadCentroCreateView | CreateView | /vat/centros/<id>/actividades/nueva/ |
| ActividadCentroDetailView | DetailView | /vat/centros/actividades/<pk>/detalle/ |
| ActividadCentroUpdateView | UpdateView | /vat/centros/actividades/<pk>/editar/ |
| ParticipanteActividadCreateView | CreateView | /vat/centros/<id>/actividades/<id>/participantes/crear/ |
| ParticipanteActividadDeleteView | View | .../participantes/<pk>/eliminar/ |
| ParticipanteActividadListEsperaView | ListView | .../lista-espera/ |
| ParticipanteActividadPromoverView | View | .../lista-espera/<pk>/promover/ |
| RegistrarAsistenciaView | TemplateView | /vat/encuentros/<pk>/asistencia/ |
| BeneficiariosListView | ListView | /vat/beneficiarios/beneficiarios/ |
| BeneficiariosDetailView | DetailView | /vat/beneficiarios/beneficiarios/<pk>/ |
| BeneficiariosCreateView | View | /vat/beneficiarios/nuevo/ |
| ResponsableListView | ListView | /vat/beneficiarios/responsables/ |
| ResponsableDetailView | DetailView | /vat/beneficiarios/responsables/<pk>/ |
| BuscarCUILView | View | /vat/beneficiarios/buscar-cuil/ |
| BuscarResponsableView | View | /vat/beneficiarios/buscar-responsable/ |

### 7.4 API REST existente

Router DRF en `/api/vat/`:
- centros, actividades, categorias, actividades-centro, participantes
- beneficiarios, responsables, beneficiario-responsable
- provincias, municipios, localidades (read-only)

Auth: API Key (`HasAPIKey`).

### 7.5 Tests

- `VAT/tests.py` → vacío.
- Tests globales relacionados: `test_beneficiarios_service_unit.py`, `test_centro_views_unit.py`, `test_consulta_renaper_unit.py`.

---

## 9. Gap Analysis — DER v4 vs Código Actual

### 8.1 Entidades que NO existen en código

| Entidad DER v4 | Prioridad | Notas |
|---|---|---|
| organismo | ✅ Resuelto | Usar `organizaciones.Organizacion` + agregar `sigla` |
| programa_origen | ✅ Resuelto | Extender `core.Programa` + FK a Organizacion + descripcion |
| modalidad_institucional | ✅ Resuelto | Modelo nuevo (catálogo) |
| institucion | ✅ Resuelto | Extender `VAT.Centro` con campos del DER v4 |
| institucion_identificador_hist | 🟢 Baja | Historial, puede ir después |
| institucion_contacto | 🟡 Media | Hoy embebido en Centro |
| autoridad_institucional | 🟡 Media | Hoy solo referente |
| ubicacion | 🟡 Media | Hoy embebida en Centro |
| institucion_ubicacion | 🟡 Media | Hoy Centro = 1 ubicación |
| persona | ✅ Resuelto | Usar `ciudadanos.Ciudadano` (extender) |
| sector | ✅ Resuelto | Modelo nuevo (Categoria queda para actividades genéricas) |
| subsector | ✅ Resuelto | Modelo nuevo (FK a sector) |
| titulo_referencia | ✅ Resuelto | Modelo nuevo (FK a sector + subsector) |
| modalidad_cursada | ✅ Resuelto | Modelo nuevo (catálogo) |
| plan_version_curricular | ✅ Resuelto | Modelo nuevo (FK a titulo_referencia + modalidad_cursada) |
| oferta_institucional | 🔴 Alta | Entidad central del marketplace |
| evaluacion | ✅ Resuelto | Modelo nuevo (FK a comision) |
| resultado_evaluacion | ✅ Resuelto | Modelo nuevo (FK a evaluacion + inscripcion) |

### 8.2 Entidades actuales que cambian o desaparecen

| Modelo actual | Destino DER v4 | Acción |
|---|---|---|
| Centro | → institucion (extender in-place) + ubicacion + institucion_ubicacion | Extender con campos DER v4 |
| Categoria | Se mantiene | Sigue como clasificación genérica de actividades. Sector es catálogo académico nuevo |
| Actividad | → titulo_referencia + plan_version_curricular | Migrar |
| ActividadCentro | → comision (extender in-place) | ✅ Resuelto |
| ParticipanteActividad | → inscripcion (extender in-place) | ✅ Resuelto |
| Encuentro | → encuentro (extender in-place) | ✅ Resuelto |
| Asistencia | → asistencia (mantener choice, extender) | ✅ Resuelto |
| Beneficiario / Responsable | → persona (unificar) | Decisión pendiente |

### 8.3 Equivalencias parciales

| DER v4 | Código actual | Gaps |
|---|---|---|
| comision | ActividadCentro | ✅ Resuelto: extender in-place. Agregar: codigo_comision, FK oferta, FK ubicacion, requiere_voucher, monto_actividad, requiere_validacion_padron |
| comision_horario | Campos en ActividadCentro | No es entidad separada, no soporta múltiples horarios |
| encuentro | Encuentro | ✅ Resuelto: extender in-place. Agregar FK a comision_horario (nullable) |
| asistencia | Asistencia | ✅ Resuelto: mantener choice (presente/ausente/justificado), más rico que bool del DER |
| inscripcion | ParticipanteActividad | ✅ Resuelto: extender in-place. Agregar: programa_origen, origen_canal, fecha_baja, motivo_baja, validacion_presencial |
| persona | Ciudadano | ✅ Resuelto: usar ciudadanos.Ciudadano. Agregar: nivel_estudio_maximo, domicilio_actual_confirmado |

---

## 10. Plan de Implementación

> ⚠️ Pendiente: definir con el equipo la estrategia (migración progresiva vs rewrite).

### 9.1 Estrategia sugerida

Migración progresiva en fases, manteniendo retrocompatibilidad.

### 9.2 Fases tentativas

**Fase 1 — Maestras institucionales**
- Crear: organismo, programa_origen, modalidad_institucional
- Fixtures iniciales

**Fase 2 — Institución y estructura territorial**
- Crear: institucion, ubicacion, institucion_ubicacion
- Migrar datos de Centro → institucion + ubicacion
- Crear: institucion_contacto, autoridad_institucional
- Opcional: institucion_identificador_hist

**Fase 3 — Catálogos académicos**
- Crear: sector, subsector, titulo_referencia, modalidad_cursada, plan_version_curricular
- Migrar datos de Categoria → sector, Actividad → titulo_referencia + plan

**Fase 4 — Oferta y comisiones**
- Crear: oferta_institucional
- Migrar ActividadCentro → comision + comision_horario
- Ajustar Encuentro (FK a comision_horario)

**Fase 5 — Personas e inscripción**
- Crear/extender: persona (decisión sobre Ciudadano/Beneficiario/Responsable)
- Migrar ParticipanteActividad → inscripcion
- Ajustar Asistencia

**Fase 6 — Voucher y Validación**
- Crear: voucher_config_programa, voucher_saldo, voucher_movimiento
- Crear: padron_programa
- Agregar campos requiere_voucher, monto_actividad, requiere_validacion_padron a comision/ActividadCentro
- Integrar validaciones en flujo de inscripción
- Proceso automático de recarga (celery task)
- Sección voucher en legajo ciudadano

**Fase 7 — Evaluaciones**
- Crear: evaluacion, resultado_evaluacion

---

## 11. Decisiones Técnicas

### 11.1 Decisiones tomadas

- Soft delete via `SoftDeleteModelMixin` (patrón del proyecto).
- Servicios en `services/` por dominio con patrón `impl.py` + `__init__.py`.
- Filtros avanzados via `AdvancedFilterEngine` (patrón del proyecto).
- API REST con DRF + API Key auth.
- Consulta RENAPER con cache en sesión + modelo persistente.
- Class Based Views (patrón del proyecto).

### 11.2 Reutilización de entidades existentes

#### programa_origen → Extender `core.models.Programa` (Opción 1 ✅)

El modelo `core.models.Programa` ya existe en el sistema:

```python
class Programa(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    estado = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=500, null=True, blank=True)
```

**Lo que tiene:** nombre (único), estado (activo/inactivo), observaciones.
**Lo usa:** `core.MontoPrestacionPrograma` (FK), `comedores` tiene su propio `Programas` local.
**Ya tiene CRUD** de `MontoPrestacionPrograma` asociado en core/views y core/urls.

**Campos a agregar para cumplir con DER v4:**
- `organismo` (FK a organismo, nullable al inicio)
- `descripcion` (TextField, nullable)

**No se toca:** la config de voucher/inscripción queda en `voucher_config_programa` (tabla separada con FK a Programa).

**Decisión:** extender `core.Programa` con lo mínimo. No crear modelo nuevo.

#### institucion → Extender `VAT.Centro` (Opción 1 ✅)

El modelo `VAT.models.Centro` ya existe y tiene CRUD completo, vistas, API, permisos, templates, servicios y filtros.

**Lo que tiene:**
- ✅ nombre, codigo (unique), activo, foto
- ✅ FK a Organizacion (organizacion_asociada)
- ✅ FK a User (referente) con limit_choices_to grupo
- ✅ Ubicación: provincia, municipio, localidad, calle, numero, domicilio_actividad
- ✅ Contacto: telefono, celular, correo, sitio_web, link_redes
- ✅ Referente: nombre_referente, apellido_referente, telefono_referente, correo_referente
- ✅ Soft delete, GinIndex en nombre

**Campos a agregar para cumplir con DER v4 (`institucion`):**

| Campo | Tipo | Descripción |
|---|---|---|
| modalidad_institucional | FK | FK a modalidad_institucional (nueva entidad) |
| tipo_gestion | VARCHAR(50) | Tipo de gestión |
| clase_institucion | VARCHAR(50) | Clase de institución |
| situacion | VARCHAR(50) | Situación actual |
| fecha_alta | DATE | Fecha de alta en el sistema |

**Lo que NO se toca:**
- Contacto embebido se mantiene por ahora. Migración a `institucion_contacto` es opcional/futura.
- Ubicación embebida se mantiene. Migración a `ubicacion` + `institucion_ubicacion` es opcional/futura.
- Autoridad (referente) se mantiene. Migración a `autoridad_institucional` es opcional/futura.

**Decisión:** extender `VAT.Centro` in-place. No crear modelo nuevo. No renombrar.

#### organismo → Evaluar `organizaciones.models.Organizacion`

El modelo `organizaciones.models.Organizacion` ya existe:

```python
class Organizacion(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=255)
    cuit = models.BigIntegerField(unique=True, null=True)
    telefono, email, domicilio, localidad, provincia, municipio
    tipo_entidad → TipoEntidad → SubtipoEntidad
    fecha_vencimiento, fecha_creacion
```

**Lo que tiene:** nombre, CUIT, contacto, ubicación, tipo/subtipo de entidad, soft delete.
**Ya se usa en VAT:** `Centro.organizacion_asociada` es FK a `Organizacion`.
**Jerarquía existente:** `TipoEntidad` → `SubtipoEntidad` (clasificación de organizaciones).

**Comparación con `organismo` del DER v4:**

| Atributo DER v4 | ¿Existe en Organizacion? | Notas |
|---|---|---|
| nombre | ✅ | Existe |
| sigla | ❌ | No tiene, se puede agregar |
| tipo | ⚠️ | Tiene `tipo_entidad` (FK), DER v4 pide VARCHAR. Más rico que el DER |
| activo | ⚠️ | Tiene soft delete, no un bool `activo`. Se puede resolver con `is_active` o el soft delete |

**Evaluación:**
`Organizacion` es más completa que `organismo` del DER v4 (tiene CUIT, ubicación, contacto, tipo/subtipo).
Puede funcionar como organismo si se le agrega `sigla`.
VAT ya la usa (`Centro.organizacion_asociada`), así que la relación ya existe.

#### organismo → Usar `organizaciones.Organizacion` (Opción 1 ✅)

Se usa `organizaciones.models.Organizacion` como equivalente a `organismo` del DER v4.
- Agregar campo `sigla` (VARCHAR 30, nullable) a `Organizacion`.
- Usar `tipo_entidad` para distinguir organismos rectores de otras organizaciones.
- FK desde `Programa.organismo → Organizacion`.
- No se crea modelo nuevo.

#### inscripcion → Extender `VAT.ParticipanteActividad` (Opción 1 ✅)

El modelo `VAT.models.ParticipanteActividad` ya vincula `Ciudadano` con `ActividadCentro` (futura `comision`).

**Lo que tiene:**
- ✅ FK a Ciudadano (persona)
- ✅ FK a ActividadCentro (comision)
- ✅ estado (inscrito/lista_espera/dado_baja)
- ✅ fecha_inscripcion
- ✅ Historial de cambios via ParticipanteActividadHistorial
- ✅ Soft delete, unique_together (ciudadano, actividad_centro)

**Campos a agregar para cumplir con DER v4 (`inscripcion`):**

| Campo | Tipo | Descripción |
|---|---|---|
| programa_origen | FK | FK a core.Programa (nullable, para trazabilidad del programa) |
| origen_canal | VARCHAR(30) | Canal de inscripción: web / presencial / importacion |
| fecha_validacion_presencial | DATE | Fecha de validación presencial (nullable) |
| fecha_baja | DATE | Fecha efectiva de baja (nullable) |
| motivo_baja | VARCHAR(200) | Motivo de la baja (nullable) |

**Integración con voucher:** al inscribirse se valida saldo y se crea `voucher_movimiento` (débito). Al dar de baja se reintegra (crédito).
**Integración con padrón:** se valida DNI del ciudadano contra `padron_programa` del programa.
**Integración con tipo_inscripcion:** se valida si el programa permite inscripción única o múltiple.

**Decisión:** extender `ParticipanteActividad` in-place. No crear modelo nuevo.

#### sector → Modelo nuevo (no reusar Categoria)

`VAT.Categoria` se usa como clasificación genérica de actividades (deportes, cultura, etc.).
`sector` del DER v4 es el primer nivel del catálogo académico: sector → subsector → titulo_referencia → plan_version_curricular.

Son conceptos distintos. Categoria se mantiene para actividades genéricas. Sector es un catálogo nuevo.

**Decisión:** crear modelo nuevo `Sector` en VAT. No reusar ni migrar Categoria.

#### persona → Usar `ciudadanos.Ciudadano` (Opción 1 ✅)

El modelo `ciudadanos.models.Ciudadano` ya existe y es usado por VAT en `ParticipanteActividad.ciudadano`.

**Lo que tiene:**
- ✅ apellido, nombre, fecha_nacimiento, documento (DNI)
- ✅ sexo (FK a core.Sexo), nacionalidad (FK)
- ✅ email, telefono
- ✅ domicilio: calle, altura, piso, depto, provincia, municipio, localidad
- ✅ estado_civil, cuil_cuit, foto
- ✅ origen_dato (≈ origen_validacion del DER)
- ✅ Soft delete
- ✅ CiudadanoPrograma (vincula ciudadano↔programa con historial)

**Campos a agregar para cumplir con DER v4 (`persona`):**

| Campo | Tipo | Descripción |
|---|---|---|
| nivel_estudio_maximo | VARCHAR(100) | Nivel de estudio máximo alcanzado (nullable) |
| domicilio_actual_confirmado | BOOLEAN | Si el domicilio actual fue confirmado (default False) |

**Decisión:** usar `ciudadanos.Ciudadano` como `persona`. No crear modelo nuevo.

#### comision → Extender `VAT.ActividadCentro` (Opción 1 ✅)

El modelo `VAT.models.ActividadCentro` ya vincula actividad con centro, tiene cupo, estado, fechas, días y horarios.

**Lo que tiene:**
- ✅ FK a Centro (institucion) y Actividad
- ✅ cupo, estado (planificada/en_curso/finalizada)
- ✅ fecha_inicio, fecha_fin
- ✅ dias (M2M a core.Dia), hora_inicio, hora_fin
- ✅ Soft delete

**Campos a agregar para cumplir con DER v4 (`comision`):**

| Campo | Tipo | Descripción |
|---|---|---|
| codigo_comision | VARCHAR(50) | Código identificador de la comisión (nullable) |
| oferta_institucional | FK | FK a oferta_institucional (nullable al inicio) |
| institucion_ubicacion | FK | FK a institucion_ubicacion (nullable, futura) |
| requiere_voucher | BOOLEAN | Si la actividad tiene costo (default False) |
| monto_actividad | DECIMAL(10,2) | Monto que descuenta del voucher (nullable) |
| requiere_validacion_padron | BOOLEAN | Si requiere estar en padrón (default False) |

**Decisión:** extender `ActividadCentro` in-place. No crear modelo nuevo.

#### encuentro → Extender `VAT.Encuentro` (Opción 1 ✅)

El modelo ya tiene fecha, hora_desde, hora_hasta, estado, observaciones, FK a ActividadCentro.

**Campo a agregar:**

| Campo | Tipo | Descripción |
|---|---|---|
| comision_horario | FK | FK a comision_horario (nullable, para vincular con horario específico) |

**Decisión:** extender `Encuentro` in-place.

#### asistencia → Extender `VAT.Asistencia` (mantener choice ✅)

El DER v4 usa `presente` (bool). El código actual usa choice: presente / ausente / justificado.
El choice es más rico y ya está implementado.

**Decisión:** mantener choice actual. No degradar a bool. Extender si se necesitan campos adicionales.

#### Modelos nuevos a crear

| Modelo | App | FKs | Atributos clave |
|---|---|---|---|
| Sector | VAT | — | nombre, descripcion |
| Subsector | VAT | sector_id → Sector | nombre, descripcion |
| TituloReferencia | VAT | sector_id → Sector, subsector_id → Subsector | codigo_referencia, nombre, descripcion, activo |
| ModalidadCursada | VAT | — | nombre, descripcion, activo |
| PlanVersionCurricular | VAT | titulo_referencia_id → TituloReferencia, modalidad_cursada_id → ModalidadCursada | normativa, version, horas_reloj, nivel_requerido, nivel_certifica, frecuencia, activo |
| ModalidadInstitucional | VAT | — | nombre, descripcion, activo |
| Evaluacion | VAT | comision_id → ActividadCentro | tipo, nombre, fecha, es_final |
| ResultadoEvaluacion | VAT | evaluacion_id → Evaluacion, inscripcion_id → ParticipanteActividad | aprobo, fecha_registro |

### 11.3 Decisiones pendientes

- ¿Se unifica Beneficiario + Responsable → Ciudadano? (Ciudadano ya es persona)
- ¿Se mantiene el flujo de beneficiarios/responsables con RENAPER o se absorbe en persona?
- ¿Cómo se maneja la coexistencia durante la migración?
- oferta_institucional: ¿modelo nuevo o extender algo existente?

---

## 12. Endpoints API

### 11.1 API actual (DRF ViewSets)

Base: `/api/vat/`

| Recurso | Métodos | Auth |
|---|---|---|
| centros/ | CRUD + activos/ | API Key |
| actividades/ | CRUD | API Key |
| categorias/ | CRUD | API Key |
| actividades-centro/ | CRUD + por_centro/ | API Key |
| participantes/ | CRUD + cambiar_estado/ | API Key |
| beneficiarios/ | CRUD + por_responsable/ | API Key |
| responsables/ | CRUD | API Key |
| beneficiario-responsable/ | CRUD | API Key |
| provincias/ | Read-only | API Key |
| municipios/ | Read-only | API Key |
| localidades/ | Read-only | API Key |

### 11.2 Endpoints pendientes (DER v4)

> ⚠️ Se definirán a medida que se implementen las nuevas entidades.

---

## 13. Changelog del Documento

| Fecha | Cambio |
|---|---|
| 2025-06 | Creación inicial con matriz maestra DER v4, descripción de entidades, estado actual de implementación y gap analysis |
| 2025-06 | Agregada sección 6: Voucher (config por programa, saldo por ciudadano, movimientos) y Validación de Inscripción contra padrón por programa |
| 2025-06 | Agregado tipo_inscripcion (unica/multiple) en config de programa con reglas y flujo actualizado |
| 2025-06 | Decisión: programa_origen → extender core.Programa. organismo → usar organizaciones.Organizacion. institucion → extender VAT.Centro |
| 2025-06 | Decisión: inscripcion → extender VAT.ParticipanteActividad. sector → modelo nuevo (Categoria se mantiene aparte) |
| 2025-06 | Decisión masiva: persona → ciudadanos.Ciudadano. comision → extender ActividadCentro. encuentro → extender Encuentro. asistencia → mantener choice. Modelos nuevos: Sector, Subsector, TituloReferencia, ModalidadCursada, PlanVersionCurricular, ModalidadInstitucional, Evaluacion, ResultadoEvaluacion |
