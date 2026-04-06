# Manual de Usuario — Módulo VAT

## ¿Qué es este módulo?

El módulo **VAT** gestiona dos grandes áreas complementarias:

1. **Formación profesional** — Centros de Formación Profesional (CFP), su oferta educativa (ofertas, comisiones, horarios), inscripciones y evaluaciones.
2. **Sistema de vouchers** — Créditos de formación asignados a ciudadanos para que accedan a cursos. Incluye parametrías, asignación individual y masiva, recargas y auditoría.

> **Ejemplo de uso completo:** El Ministerio lanza el programa "Formación 2026". Se crea una parametría que otorga 5 créditos por ciudadano con vencimiento 31/12/2026. Se asignan masivamente a 300 beneficiarios cargando una lista de DNIs. Cada beneficiario usa sus créditos al inscribirse a una comisión en un CFP habilitado.

---

## Flujo general de trabajo

```
Catálogos → Centros → Datos Institución → Oferta Educativa → Vouchers → Inscripciones → Evaluaciones
```

- Para **habilitar un CFP**: Catálogos → Centros → Datos Institución → Oferta Educativa.
- Para **gestionar vouchers**: Parametrías → Asignación (individual o masiva) → Uso automático al inscribirse.
- El trabajo diario se concentra en **Inscripciones, Vouchers y Evaluaciones**.

---

## 1. Catálogos

Tablas de referencia que se configuran una vez y rara vez cambian. Deben cargarse antes de crear cualquier oferta educativa.

### 1.1 Modalidades Institucionales

Define el tipo de institución del centro.

**Campos:**
- **Nombre** *(obligatorio)*: nombre de la modalidad
- **Descripción** *(opcional)*
- **Activo**: si está disponible para ser usada

> **Ejemplo:** "Institución Pública", "Privada con fines de lucro", "Cooperativa de Trabajo", "ONG".

**Cuándo usarlo:** antes de cargar centros. Cada centro debe tener su modalidad asignada.

---

### 1.2 Sectores

Agrupa las familias ocupacionales.

**Campos:**
- **Nombre** *(obligatorio)*
- **Descripción** *(opcional)*

> **Ejemplo:** Sector "Construcción" agrupa títulos como "Electricista", "Plomero", "Albañil". Sector "Gastronomía" agrupa "Cocinero", "Pastelero", "Barista".

**Cuándo usarlo:** antes de cargar Títulos de Referencia.

---

### 1.3 Títulos de Referencia

Son los títulos oficiales que puede dictar un CFP. Cada título pertenece a un sector.

**Campos:**
- **Sector** *(obligatorio)*: a qué sector pertenece
- **Subsector** *(opcional)*: subdivisión del sector
- **Nombre** *(obligatorio)*: nombre oficial del título
- **Código de referencia** *(opcional)*: código externo o normativo
- **Descripción** *(opcional)*
- **Activo**

> **Ejemplo:** Título "Electricista Instalador de Baja Tensión" en el sector "Electricidad". Título "Gastronomía Básica" en el sector "Gastronomía". El código de referencia puede ser la resolución ministerial que lo avala (ej: `RES-2019-142`).

**Cuándo usarlo:** antes de crear Planes Curriculares.

---

### 1.4 Planes Curriculares

Un plan curricular es la versión específica de un título con su modalidad de cursada, horas y normativa.

**Campos:**
- **Título de referencia** *(obligatorio)*
- **Modalidad de cursada** *(obligatorio)*: presencial, virtual, híbrido
- **Normativa** *(opcional)*: resolución o normativa que lo regula
- **Versión** *(opcional)*: identificador de versión
- **Horas reloj** *(opcional)*: duración total
- **Nivel requerido / que certifica** *(opcionales)*
- **Frecuencia** *(opcional)*
- **Activo**

> **Ejemplo:** El título "Gastronomía Básica" tiene dos planes: uno presencial de 200 hs (Versión 1 - Res. 2019) y uno virtual de 160 hs (Versión 2 - Res. 2023). El CFP puede elegir cuál dictar según su equipamiento.

---

## 2. Centros de Formación

Entidad principal del módulo. Representa un CFP habilitado.

**Campos principales:**
- **Nombre** *(obligatorio)*
- **Código** *(obligatorio, único)*: código identificador del centro
- **Referente** *(obligatorio)*: usuario del sistema responsable
- **Modalidad institucional**
- **Domicilio de actividad** *(obligatorio)*
- **Teléfono / Celular / Correo** *(obligatorios)*
- **Nombre, teléfono y correo del referente** *(obligatorios)*
- **Provincia / Municipio / Localidad**
- **Activo**

> **Ejemplo:** Centro "CFP N° 12 — La Plata", código `CFP-LP-012`, referente Juan Pérez, modalidad "Institución Pública", domicilio Calle 7 N° 123, La Plata.

Desde el detalle del centro se accede a todas sus inscripciones, ofertas y actividades.

---

## 3. Datos Institución

Datos complementarios del centro. Se accede desde el detalle del centro una vez creado.

### 3.1 Contactos

Permite registrar responsables y contactos institucionales en una sola tabla.

**Campos:**
- **Centro** *(obligatorio)*
- **Nombre y apellido del responsable**
- **Rol / Área**
- **Documento**
- **Teléfono / Correo electrónico**
- **Es principal**
- **Observaciones**

> **Ejemplo:** El CFP N° 12 registra a María González como responsable principal de Dirección con DNI 28.456.789, correo `direccion@cfp12.test` y un teléfono alternativo de secretaría en una segunda fila institucional.

---

### 3.2 Identificadores

Registra los códigos oficiales del centro con historial de cambios.

**Campos:**
- **Centro** *(obligatorio)*
- **Tipo de identificador** *(obligatorio)*: CUIE, CUE, código provincial, CUIT, otro
- **Valor** *(obligatorio)*
- **Rol institucional**: sede, anexo, polo, centro de formación
- **Es actual**
- **Vigencia desde / hasta**
- **Motivo**: razón del cambio

> **Ejemplo:** El CFP N° 12 tiene CUIE `062-0012`, CUE `060123456` y CUIT `30-71234567-8`. Si el CUE fue reasignado en 2022, se registran ambos: el anterior con `es actual = no` y el nuevo con `es actual = sí`, con el motivo "Reasignación jurisdiccional".

---

### 3.3 Ubicaciones

Múltiples domicilios del centro (sede, anexos, puntos de atención).

**Campos:**
- **Centro** *(obligatorio)*
- **Localidad** *(obligatorio)*
- **Rol de la ubicación** *(obligatorio)*: sede principal, anexo, dependencia, punto de atención
- **Domicilio** *(opcional)*
- **Es principal**
- **Latitud / Longitud** *(opcionales)*
- **Vigencia desde / hasta**

> **Ejemplo:** El CFP N° 12 tiene su sede principal en Calle 7 N° 123 (es principal = sí) y un anexo en el barrio Olmos, Av. 44 N° 890 (rol: anexo, es principal = no).

---

## 4. Oferta Educativa

Todo lo relacionado con los cursos que ofrece un centro.

### 4.1 Ofertas Institucionales

Propuesta formal de un centro de dictar un plan curricular en un ciclo lectivo. Es el nivel más alto de la cadena educativa.

**Campos:**
- **Centro** *(obligatorio)*
- **Plan curricular** *(obligatorio)*
- **Programa** *(obligatorio)*
- **Ciclo lectivo** *(obligatorio)*: año
- **Nombre local** *(opcional)*
- **Estado** *(obligatorio)*: planificada → aprobada → publicada → cerrada / cancelada
- **Aprobación jurisdicción / INET**
- **Fecha de publicación** *(opcional)*
- **Observaciones**

> **Ejemplo:** El CFP N° 12 propone dictar "Electricista Instalador de Baja Tensión" (Plan presencial 200hs, Programa "Formación 2026") en el ciclo 2026. Estado inicial: `planificada`. Una vez aprobada por jurisdicción, pasa a `aprobada`, y cuando se publican las inscripciones, a `publicada`.

---

### 4.2 Comisiones

Un grupo de alumnos dentro de una oferta institucional. Tiene su propio cupo, fechas y horarios.

**Campos:**
- **Oferta institucional** *(obligatorio)*
- **Código de comisión** *(obligatorio, único)*
- **Nombre** *(obligatorio)*
- **Ubicación** *(opcional)*
- **Fecha de inicio / fin** *(obligatorio)*
- **Cupo** *(obligatorio)*: máximo de alumnos (debe ser > 0)
- **Estado**: planificada → activa → cerrada / suspendida
- **Observaciones**

> **Ejemplo:** La oferta de "Electricista" tiene dos comisiones: "Comisión A — Turno Mañana" (código `ELEC-2026-A`, cupo 20, lunes/miércoles/viernes 8-12hs) y "Comisión B — Turno Noche" (código `ELEC-2026-B`, cupo 15, lunes/jueves 19-23hs).

---

### 4.3 Actividades

Actividades complementarias que organiza el centro (talleres, charlas, eventos) fuera de la oferta curricular formal.

**Campos:**
- **Centro** *(obligatorio)*
- **Actividad** *(obligatorio)*: tipo de actividad del catálogo
- **Cantidad de personas** estimadas
- **Días y horarios**
- **Precio** *(opcional)*
- **Estado**: planificada, en curso, finalizada
- **Fecha inicio / fin**

> **Ejemplo:** El CFP N° 12 organiza una "Jornada de Orientación Laboral" para 50 personas, sin costo, el 15 de abril. Desde el detalle se registran los encuentros y la asistencia.

---

### 4.4 Oferta Formativa

Curso abierto con cupos, fechas y costo, vinculado al sistema de vouchers. Diferente de la Oferta Institucional (que es el registro formal ante INET).

**Campos:**
- **Centro** *(obligatorio)*
- **Plan curricular** *(obligatorio)*
- **Fecha inicio / fin** *(obligatorio)*
- **Cantidad de cupos** *(obligatorio)*
- **Horario desde / hasta** *(obligatorio)*
- **Días de la semana**
- **Costo por participante** *(opcional)*
- **Estado**: planificada, abierta, cerrada

> **Ejemplo:** El CFP N° 12 abre una Oferta Formativa de "Gastronomía Básica", 20 cupos, del 01/05/2026 al 31/07/2026, martes y jueves de 14 a 18hs, costo 0 (subsidiado por voucher). Los ciudadanos con voucher disponible pueden inscribirse y el sistema descuenta créditos automáticamente.

---

## 5. Sistema de Vouchers

Los vouchers son créditos de formación que se asignan a ciudadanos para que accedan a cursos gratuitos o subsidiados. El flujo es: **Crear parametría → Asignar vouchers → El ciudadano usa los créditos al inscribirse**.

### 5.1 Parametrías de Voucher

Una parametría es la plantilla que define las condiciones del voucher: cuántos créditos otorga, cuándo vence y cómo se renueva. Desde una misma parametría se pueden generar vouchers para miles de ciudadanos.

**Campos:**
- **Nombre** *(obligatorio)*: nombre descriptivo de la parametría
- **Descripción** *(opcional)*
- **Programa** *(obligatorio)*: programa al que pertenece
- **Créditos por ciudadano** *(obligatorio)*: cuántos créditos recibe cada beneficiario (debe ser > 0)
- **Fecha de vencimiento** *(obligatorio)*: hasta cuándo son válidos los créditos (debe ser futura)
- **Renovación mensual**: si los créditos se recargan automáticamente cada mes
- **Créditos en cada renovación** *(opcional)*: si está vacío, se usa la cantidad inicial
- **Tipo de renovación**:
  - `Sumar al saldo existente`: agrega créditos encima del saldo que tenga
  - `Reiniciar al valor configurado`: resetea el saldo al valor de renovación
- **Activa**: si está disponible para asignar vouchers

> **Ejemplo:** Parametría "Formación 2026 — Electricidad", Programa "Formación 2026", 5 créditos por ciudadano, vencimiento 31/12/2026, renovación mensual activada, 2 créditos/mes tipo "sumar". Un beneficiario empieza con 5 créditos; cada mes se le suman 2 más (tope real según disponibilidad).

**Desde el detalle de una parametría** se visualizan:
- Uso total de créditos emitidos vs. usados
- Distribución de vouchers por estado (activos, agotados, vencidos, cancelados)
- Últimas asignaciones realizadas
- Acciones: asignar individual o masivamente

---

### 5.2 Vouchers — Asignación Individual

Asigna un voucher a un ciudadano específico desde la parametría o de forma manual.

**Desde una parametría:**
1. Ir al detalle de la parametría.
2. Ingresar el DNI del ciudadano en el campo de asignación individual.
3. Confirmar. El sistema crea el voucher con los parámetros de la parametría.

**Manual (sin parametría):**
1. Ir a **Vouchers → Nuevo Voucher**.
2. Seleccionar ciudadano, programa, cantidad inicial y fecha de vencimiento.
3. Guardar.

> **Ejemplo:** El operador busca el DNI `28456789` (María González) en la parametría "Formación 2026 — Electricidad" y confirma. El sistema le asigna 5 créditos con vencimiento 31/12/2026. Si María ya tenía un voucher activo de esa parametría, el sistema avisa y no crea uno duplicado.

**Estados del voucher:**
- `Activo`: tiene créditos disponibles y no venció
- `Agotado`: usó todos sus créditos
- `Vencido`: superó la fecha de vencimiento
- `Cancelado`: dado de baja manualmente

---

### 5.3 Vouchers — Asignación Masiva

Permite asignar vouchers a múltiples ciudadanos a la vez cargando una lista de DNIs.

**Pasos:**
1. Ir al detalle de la parametría.
2. Hacer clic en **Asignar masivamente**.
3. Ingresar los DNIs separados por coma, punto y coma, espacio o salto de línea (hasta 500 por vez).
4. Confirmar. El sistema procesa cada DNI y reporta:
   - **Asignados**: voucher creado correctamente
   - **Reactivados**: tenía voucher vencido/agotado y fue renovado
   - **Ya tenían voucher activo**: se omitieron sin error
   - **No encontrados**: el DNI no existe en el sistema
   - **Con error**: fallo inesperado

> **Ejemplo:** Se carga la lista de 280 DNIs del padrón del programa. El sistema reporta: 265 asignados, 8 reactivados (tenían voucher vencido del año anterior), 5 ya tenían voucher activo, 2 no encontrados (DNIs con error tipográfico).

---

### 5.4 Recargas de Voucher

Permite agregar créditos a un voucher existente de forma manual, o son generadas automáticamente si la parametría tiene renovación mensual activa.

**Motivos de recarga:**
- `Automática`: generada por el sistema mensualmente
- `Manual`: realizada por un operador
- `Ajuste`: corrección de un error
- `Compensación`: créditos adicionales por algún inconveniente

> **Ejemplo:** María González usó sus 5 créditos en enero pero todavía está dentro del período del programa. El operador hace una recarga manual de 3 créditos con motivo "compensación" por un curso cancelado. El sistema registra la recarga y el saldo queda en 3 créditos disponibles.

---

### 5.5 Log de Auditoría

Cada evento sobre un voucher queda registrado automáticamente y no puede modificarse. Los eventos son: asignación, recarga, uso, vencimiento y cancelación.

> **Ejemplo:** El log de María González muestra: 01/01/2026 — asignación (5 créditos), 15/02/2026 — uso (-1 crédito, inscripción al curso de Electricidad), 15/02/2026 — uso (-1 crédito, inscripción al curso de Soldadura), 01/03/2026 — recarga automática (+2 créditos).

---

## 6. Personas

Registro central de las personas que participan en los programas. Puede estar vinculada a un ciudadano ya existente.

**Campos:**
- **DNI** *(obligatorio, único)*
- **Nombre / Apellido** *(obligatorio)*
- **Fecha de nacimiento** *(obligatorio)*
- **Género** *(opcional)*
- **Email / Teléfono** *(opcionales)*
- **Nivel de estudio máximo** *(opcional)*
- **Domicilio según DNI / actual** *(opcionales)*

> **Ejemplo:** Antes de inscribir a Pedro Ramírez (DNI 33.111.222) a una comisión, se busca su DNI en Personas. Si no existe, se lo crea con sus datos. Si ya existe de una inscripción anterior, se usa el registro existente.

**Flujo habitual:** buscar por DNI → si no existe, crear → luego inscribir.

---

## 7. Inscripciones

Registra la inscripción de una **Persona** a una **Comisión**. Es el registro principal de participación en un curso formal.

**Campos:**
- **Persona** *(obligatorio)*
- **Comisión** *(obligatorio)*
- **Programa** *(obligatorio)*
- **Estado** *(obligatorio)*:
  - `pre_inscripta`: registrada pero no confirmada
  - `inscripta`: confirmada
  - `validada_presencial`: confirmó asistencia en persona
  - `completada`: finalizó el curso
  - `abandonada`: dejó el curso
  - `rechazada`: no fue aceptada
- **Canal de origen**: front público, backoffice, API, importación
- **Fecha de inscripción**: automática
- **Observaciones**

> **Ejemplo:** Pedro Ramírez se inscribe a la "Comisión A — Turno Mañana" del curso de Electricidad. Estado inicial: `inscripta`. Al finalizar el curso con aprobación, se actualiza a `completada`. Si abandona a mitad de camino, se registra como `abandonada`.

> Una persona no puede inscribirse dos veces a la misma comisión.

---

## 8. Evaluaciones

Define las instancias de evaluación de una comisión.

**Campos:**
- **Comisión** *(obligatorio)*
- **Tipo** *(obligatorio)*: parcial, final, integradora, recuperatorio
- **Nombre** *(obligatorio)*
- **Descripción** *(opcional)*
- **Fecha** *(obligatorio)*
- **Es final**: si es la evaluación final del curso
- **Ponderación**: peso en la nota final (0 a 100)
- **Observaciones**

> **Ejemplo:** La "Comisión A — Electricidad" tiene 3 evaluaciones: "Primer parcial práctico" (ponderación 30, no es final), "Segundo parcial práctico" (ponderación 30, no es final) y "Evaluación final integradora" (ponderación 40, es final = sí).

---

## 9. Resultados de Evaluación

Calificación de cada inscripto en cada evaluación.

**Campos:**
- **Evaluación** *(obligatorio)*
- **Inscripción** *(obligatorio)*: alumno vinculado a su inscripción
- **Calificación** *(opcional)*: nota numérica
- **Aprobó**: sí / no / sin dato
- **Observaciones**
- **Registrado por**: automático

> **Ejemplo:** Para la "Evaluación final integradora" de la Comisión A, se cargan los resultados de los 20 alumnos inscriptos. Pedro Ramírez obtuvo 8.5 y aprobó = sí. Lucía Fernández obtuvo 3.0 y aprobó = no, quedando pendiente el recuperatorio.

---

## Flujos de uso frecuente

### Alta de un nuevo centro

1. Verificar en **Catálogos → Modalidades Institucionales** que exista la modalidad correcta.
2. Ir a **Centros de Formación → Agregar Centro** y completar los datos.
3. Desde el detalle del centro, completar **Datos Generales**: contactos institucionales, identificadores y ubicaciones.

---

### Armar la oferta de un ciclo lectivo

1. Verificar que el **Plan Curricular** exista en **Catálogos → Planes Curriculares**. Si no, crearlo desde el **Título de Referencia** correspondiente.
2. Ir a **Oferta Educativa → Ofertas Institucionales → Agregar**.
3. Seleccionar centro, plan curricular, programa y ciclo lectivo.
4. Una vez creada la oferta, agregar **Comisiones** desde el detalle de la oferta.
5. Para cada comisión, agregar horarios desde el detalle de la comisión.

---

### Lanzar un programa de vouchers

1. Ir a **Vouchers → Parametrías → Nueva Parametría**.
2. Configurar nombre, programa, créditos, vencimiento y renovación.
3. Desde el detalle de la parametría, usar **Asignar masivamente** para cargar la lista de DNIs beneficiarios.
4. Revisar el reporte de asignación: asignados, omitidos, no encontrados.
5. El sistema gestiona automáticamente los usos cuando los ciudadanos se inscriben a ofertas formativas.

---

### Inscribir una persona a un curso

1. Ir a **Personas** y buscar por DNI. Si no existe, crearla.
2. Ir a **Inscripciones → Nueva Inscripción**.
3. Seleccionar persona, comisión y programa.
4. Establecer el estado inicial.
5. Guardar. Si la comisión está vinculada al sistema de vouchers, los créditos se descuentan automáticamente.

---

### Registrar resultados de evaluación

1. Verificar que la evaluación exista en **Evaluaciones** para esa comisión. Si no, crearla.
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
| Oferta institucional | Propuesta anual de un CFP de dictar un plan ante INET |
| Oferta formativa | Curso abierto con cupos para el sistema de vouchers |
| Comisión | Grupo de alumnos dentro de una oferta |
| Ciclo lectivo | Año de cursada |
| Cupo | Cantidad máxima de alumnos por comisión |
| Voucher | Crédito de formación asignado a un ciudadano |
| Parametría | Plantilla que define las condiciones de un voucher |
| Crédito | Unidad de uso de un voucher (descuenta al inscribirse) |
| Renovación | Recarga automática mensual de créditos según parametría |
| Ponderación | Peso de una evaluación en la nota final |
| Canal de origen | Cómo se realizó la inscripción (web, backoffice, API) |
