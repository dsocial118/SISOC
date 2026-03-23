# Manual de Usuario — Módulo INET (VAT)

## ¿Qué es este módulo?

El módulo **INET** gestiona la oferta de formación profesional de los Centros de Formación Profesional (CFP). Permite registrar centros, armar la propuesta educativa (ofertas, comisiones, horarios), inscribir personas a cursos y registrar sus evaluaciones.

---

## Flujo general de trabajo

El orden lógico para empezar a usar el sistema desde cero es:

```
Catálogos → Centros → Datos Institución → Oferta Educativa → Personas → Inscripciones → Evaluaciones
```

Una vez configurados los catálogos y el centro, el trabajo diario se concentra en **Personas → Inscripciones → Evaluaciones**.

---

## 1. Catálogos

Los catálogos son tablas de referencia que se configuran una vez y rara vez cambian. Deben cargarse antes de crear cualquier oferta educativa.

### 1.1 Modalidades Institucionales

Define el tipo de institución del centro (pública, privada, cooperativa, ONG, etc.).

**Campos:**
- **Nombre** *(obligatorio)*: nombre de la modalidad (ej: "Institución Pública", "Privada con fines de lucro")
- **Descripción** *(opcional)*: detalle adicional
- **Activo**: si está activa para ser usada

**Cuándo usarlo:** antes de cargar centros. Cada centro debe tener su modalidad asignada.

---

### 1.2 Sectores

Agrupa las familias ocupacionales (ej: Construcción, Industria, Servicios, Agropecuario).

**Campos:**
- **Nombre** *(obligatorio)*
- **Descripción** *(opcional)*

**Cuándo usarlo:** antes de cargar Títulos de Referencia.

---

### 1.3 Títulos de Referencia

Son los títulos oficiales que puede dictar un CFP (ej: "Electricista Instalador de Baja Tensión", "Gastronomía"). Cada título pertenece a un sector.

**Campos:**
- **Sector** *(obligatorio)*: a qué sector pertenece
- **Subsector** *(opcional)*: subdivisión del sector
- **Nombre** *(obligatorio)*: nombre oficial del título
- **Código de referencia** *(opcional)*: código externo o normativo
- **Descripción** *(opcional)*
- **Activo**: si está disponible para ser usado en planes

**Cuándo usarlo:** antes de crear Planes Curriculares.

---

### 1.4 Planes Curriculares

Un plan curricular es la versión específica de un título con su modalidad de cursada (presencial, virtual, etc.), horas y normativa aplicable.

**Campos:**
- **Título de referencia** *(obligatorio)*: el título al que pertenece
- **Modalidad de cursada** *(obligatorio)*: cómo se dicta (presencial, virtual, híbrido)
- **Normativa** *(opcional)*: resolución o normativa que lo regula
- **Versión** *(opcional)*: identificador de versión
- **Horas reloj** *(opcional)*: duración total en horas
- **Nivel requerido** *(opcional)*: nivel educativo de ingreso
- **Nivel que certifica** *(opcional)*: certificación que otorga
- **Frecuencia** *(opcional)*: ej. "3 veces por semana"
- **Activo**

> Un mismo título puede tener varios planes: uno presencial de 200 hs y otro virtual de 180 hs, por ejemplo.

---

## 2. Centros de Formación

Es la entidad principal del módulo. Representa un Centro de Formación Profesional (CFP) habilitado.

**Campos principales:**
- **Nombre** *(obligatorio)*: nombre del CFP
- **Código** *(obligatorio, único)*: código identificador del centro
- **Referente** *(obligatorio)*: usuario del sistema responsable del centro
- **Modalidad institucional**: tipo de institución
- **Domicilio de actividad** *(obligatorio)*: dirección donde funciona
- **Teléfono / Celular** *(obligatorio)*
- **Correo** *(obligatorio)*
- **Nombre y apellido del referente** *(obligatorio)*
- **Teléfono y correo del referente** *(obligatorio)*
- **Provincia / Municipio / Localidad**: ubicación geográfica
- **Activo**: si el centro está operativo

Desde la vista de detalle de un centro se accede a todas sus inscripciones, ofertas y actividades.

---

## 3. Datos Institución

Son datos complementarios del centro. Se accede a ellos una vez que el centro ya está creado. Cada sección funciona de forma independiente.

### 3.1 Contactos

Permite registrar múltiples formas de contacto de un centro (correos alternativos, redes sociales, sitio web, etc.), además de los que ya tiene el registro principal.

**Campos:**
- **Centro** *(obligatorio)*
- **Tipo** *(obligatorio)*: email, teléfono, celular, sitio web, redes sociales
- **Valor** *(obligatorio)*: el dato de contacto
- **Es principal**: si es el contacto preferido de ese tipo
- **Observaciones**

---

### 3.2 Autoridades

Registra las autoridades institucionales (director, coordinador, representante legal) del centro con su vigencia.

**Campos:**
- **Centro** *(obligatorio)*
- **Nombre completo** *(obligatorio)*
- **DNI** *(obligatorio)*
- **Cargo** *(obligatorio)*
- **Email / Teléfono** *(opcionales)*
- **Es actual**: si sigue en el cargo
- **Vigencia desde / hasta**: período de ejercicio del cargo

---

### 3.3 Identificadores

Registra los códigos oficiales del centro (CUIE, CUE, código provincial, CUIT, etc.) con su historial de cambios.

**Campos:**
- **Centro** *(obligatorio)*
- **Tipo de identificador** *(obligatorio)*: CUIE, CUE, código provincial, RUC, CUIT, otro
- **Valor** *(obligatorio)*: el código en sí
- **Rol institucional**: sede, anexo, polo, centro de formación
- **Es actual**: si es el identificador vigente
- **Vigencia desde / hasta**
- **Motivo**: razón del cambio (si reemplaza a uno anterior)

---

### 3.4 Ubicaciones

Permite registrar múltiples domicilios del centro (sede principal, anexos, puntos de atención) con coordenadas GPS opcionales.

**Campos:**
- **Centro** *(obligatorio)*
- **Localidad** *(obligatorio)*
- **Rol de la ubicación** *(obligatorio)*: sede principal, anexo, dependencia, punto de atención
- **Domicilio** *(opcional)*: dirección completa
- **Es principal**: si es la sede central
- **Latitud / Longitud** *(opcionales)*: para geolocalización
- **Vigencia desde / hasta**

---

## 4. Oferta Educativa

Agrupa todo lo relacionado con los cursos que ofrece un centro: su propuesta anual, las comisiones (grupos), horarios e inscripciones.

### 4.1 Ofertas Institucionales

Representa la propuesta formal de un centro de dictar un plan curricular en un ciclo lectivo. Es el nivel más alto de la cadena educativa.

**Campos:**
- **Centro** *(obligatorio)*: qué CFP la ofrece
- **Plan curricular** *(obligatorio)*: qué plan va a dictar
- **Programa** *(obligatorio)*: programa al que pertenece
- **Ciclo lectivo** *(obligatorio)*: año (ej: 2025)
- **Nombre local** *(opcional)*: nombre propio si difiere del título oficial
- **Estado** *(obligatorio)*: planificada → aprobada → publicada → cerrada / cancelada
- **Aprobación jurisdicción / INET**: checkboxes de aprobación
- **Fecha de publicación** *(opcional)*
- **Observaciones**

> La oferta institucional es anual. Las comisiones son las divisiones dentro de esa oferta.

---

### 4.2 Comisiones

Una comisión es un grupo de alumnos dentro de una oferta institucional. Tiene su propio cupo, fechas y horarios.

**Campos:**
- **Oferta institucional** *(obligatorio)*: a qué oferta pertenece
- **Código de comisión** *(obligatorio, único)*: identificador de la comisión
- **Nombre** *(obligatorio)*: ej. "Comisión A - Mañana"
- **Ubicación** *(opcional)*: dónde se dicta (vínculo con las ubicaciones del centro)
- **Fecha de inicio / fin** *(obligatorio)*
- **Cupo** *(obligatorio)*: cantidad máxima de alumnos
- **Estado**: planificada → activa → cerrada / suspendida
- **Observaciones**

---

### 4.3 Inscripciones a Oferta

> ⚠️ Esta sección es diferente de **Inscripciones** (que vincula personas a comisiones del módulo institucional). Las "Inscripciones a Oferta" son para el sistema de **Oferta Formativa** con vouchers.

Registra la inscripción de un ciudadano a una **Oferta Formativa** (ver sección 4.5).

**Campos:**
- **Oferta formativa** *(obligatorio)*
- **Ciudadano** *(obligatorio)*
- **Estado**: inscrito, lista de espera, completado, abandonado, rechazado
- **Inscripto por**: usuario que realizó la inscripción

---

### 4.4 Actividades

Actividades complementarias que organiza el centro (talleres, charlas, eventos) que no forman parte de la oferta curricular formal.

**Campos:**
- **Centro** *(obligatorio)*
- **Actividad** *(obligatorio)*: tipo de actividad (vinculado al catálogo de actividades)
- **Cantidad de personas** estimadas
- **Días y horarios**
- **Precio** *(opcional)*
- **Estado**: planificada, en curso, finalizada
- **Fecha inicio / fin**

Desde el detalle de una actividad se registran encuentros (clases) y asistencia.

---

### 4.5 Oferta Formativa

Es la oferta de un curso con cupos, fechas y costo, dirigida al sistema de vouchers. Diferente de la Oferta Institucional que es el registro formal ante INET.

**Campos:**
- **Centro** *(obligatorio)*
- **Plan curricular** *(obligatorio)*
- **Fecha inicio / fin** *(obligatorio)*
- **Cantidad de cupos** *(obligatorio)*
- **Horario desde / hasta** *(obligatorio)*
- **Días de la semana**
- **Costo por participante** *(opcional)*
- **Estado**: planificada, abierta, cerrada

---

## 5. Personas

Registro central de las personas que participan en los programas VAT/INET. Puede estar vinculada a un ciudadano ya existente en el sistema.

**Campos:**
- **DNI** *(obligatorio, único)*
- **Nombre / Apellido** *(obligatorio)*
- **Fecha de nacimiento** *(obligatorio)*
- **Género** *(opcional)*: masculino, femenino, otro, prefiere no indicar
- **Email / Teléfono** *(opcionales)*
- **Nivel de estudio máximo** *(opcional)*: sin escolaridad hasta superior completo
- **Domicilio según DNI** *(opcional)*
- **Domicilio actual** *(opcional)*

**Flujo habitual:** antes de inscribir a alguien a una comisión, hay que verificar que la persona esté registrada. Si no existe, se crea desde aquí.

---

## 6. Inscripciones

Registra la inscripción de una **Persona** a una **Comisión**. Es el registro principal de participación en un curso formal.

**Campos:**
- **Persona** *(obligatorio)*: quién se inscribe
- **Comisión** *(obligatorio)*: en qué comisión
- **Programa** *(obligatorio)*: programa al que pertenece
- **Estado** *(obligatorio)*:
  - `pre_inscripta`: registrada pero no confirmada
  - `inscripta`: confirmada
  - `validada_presencial`: confirmó asistencia en persona
  - `completada`: finalizó el curso
  - `abandonada`: dejó el curso
  - `rechazada`: no fue aceptada
- **Canal de origen**: front público, backoffice, API, importación
- **Fecha de inscripción**: se completa automáticamente
- **Observaciones**

> Una persona no puede inscribirse dos veces a la misma comisión.

---

## 7. Evaluaciones

Define las instancias de evaluación de una comisión (parciales, finales, recuperatorios, etc.).

**Campos:**
- **Comisión** *(obligatorio)*: a qué comisión pertenece
- **Tipo** *(obligatorio)*: parcial, final, integradora, recuperatorio
- **Nombre** *(obligatorio)*: ej. "Primer parcial teórico"
- **Descripción** *(opcional)*
- **Fecha** *(obligatorio)*
- **Es final**: si es la evaluación final del curso
- **Ponderación**: peso en la nota final (0 a 100)
- **Observaciones**

---

## 8. Resultados de Evaluación

Registra la calificación de cada inscripto en cada evaluación.

**Campos:**
- **Evaluación** *(obligatorio)*: de qué evaluación es el resultado
- **Inscripción** *(obligatorio)*: de qué alumno (vinculado a su inscripción a la comisión)
- **Calificación** *(opcional)*: nota numérica
- **Aprobó**: sí / no / sin dato
- **Observaciones**
- **Registrado por**: usuario que cargó el resultado (automático)

---

## Flujos de uso frecuente

### Alta de un nuevo centro

1. Ir a **Catálogos → Modalidades Institucionales** y verificar que exista la modalidad correcta.
2. Ir a **Centros de Formación → Agregar Centro**.
3. Completar datos del centro y guardar.
4. Desde el detalle del centro, completar **Datos Institución** (contactos, autoridades, identificadores, ubicaciones) según corresponda.

---

### Armar la oferta de un ciclo lectivo

1. Verificar que el **Plan Curricular** exista en **Catálogos → Planes Curriculares**. Si no, crearlo a partir del **Título de Referencia** correspondiente.
2. Ir a **Oferta Educativa → Ofertas Institucionales → Agregar**.
3. Seleccionar el centro, plan curricular, programa y ciclo lectivo.
4. Una vez creada la oferta, ir a **Comisiones → Agregar** y crear las comisiones necesarias.
5. Para cada comisión, agregar los horarios desde **Comisiones → Horarios** (si se usa esa sección separada) o directamente desde el detalle de la comisión.

---

### Inscribir una persona a un curso

1. Ir a **Personas** y buscar por DNI. Si no existe, crearla.
2. Ir a **Inscripciones → Nueva Inscripción**.
3. Seleccionar la persona, la comisión y el programa.
4. Establecer el estado inicial (`pre_inscripta` o `inscripta`).
5. Guardar.

---

### Registrar resultados de evaluación

1. Ir a **Evaluaciones** y verificar que exista la evaluación de la comisión. Si no, crearla.
2. Ir a **Resultados de Evaluación → Nuevo Resultado**.
3. Seleccionar la evaluación y la inscripción del alumno.
4. Ingresar calificación y si aprobó.
5. Guardar.

---

## Glosario

| Término | Significado |
|---|---|
| CFP | Centro de Formación Profesional |
| INET | Instituto Nacional de Educación Tecnológica |
| Plan curricular | Versión de un título con horas, modalidad y normativa |
| Oferta institucional | Propuesta anual de un CFP de dictar un plan |
| Comisión | Grupo de alumnos dentro de una oferta |
| Ciclo lectivo | Año de cursada (ej: 2025) |
| Cupo | Cantidad máxima de alumnos por comisión |
| Ponderación | Peso de una evaluación en la nota final |
| Canal de origen | Cómo se realizó la inscripción (web, backoffice, API) |
| Voucher | Crédito de horas de capacitación asignado a un ciudadano |
