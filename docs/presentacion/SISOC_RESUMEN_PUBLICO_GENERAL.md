# SISOC - Sistema de Gestión Social

**Documento de presentación para público general**

---

## ¿Qué es SISOC?

SISOC (Sistema de Información y Seguimiento de Organizaciones y Comedores) es una plataforma digital desarrollada por el Gobierno de la Provincia de Buenos Aires para gestionar los programas de asistencia alimentaria del Ministerio de Desarrollo de la Comunidad.

Es un **backoffice** —una herramienta de gestión interna— que permite a los equipos técnicos y administrativos del gobierno provincial administrar comedores, organizaciones, admisiones, relevamientos y beneficiarios de diversos programas sociales.

> **En resumen:** SISOC es el sistema que permite al gobierno provincial gestionar qué organizaciones dan de comer, a cuántas personas, con qué documentación y en qué condiciones.

---

## ¿Para qué sirve?

El sistema centraliza la gestión de los programas alimentarios, permitiendo:

- **Registrar y administrar comedores** (ubicación, estado, capacidad, organización responsable)
- **Gestionar organizaciones** (ONGs, iglesias, asociaciones civiles) que operan los comedores
- **Admitir beneficiarios** a los programas y hacer seguimiento
- **Validar documentación** legal de cada organización y comedor
- **Sincronizar datos** con sistemas externos (GESTIONAR, RENAPER)
- **Generar reportes y dashboards** para la toma de decisiones
- **Auditar cambios** en el sistema para garantizar transparencia

---

## ¿Qué programas gestiona?

El sistema soporta principalmente el **Programa Alimentar Comunidad**, que articula:

1. **Organizaciones:** Entidades jurídicas (ONGs, iglesias, asociaciones civiles) que tienen la personería y firman el convenio con el gobierno
2. **Comedores:** Espacios físicos donde se prepara y distribuye la comida

Otros programas asociados:
- Centro de Familia
- Centro de Infancia
- Celiaquía (programa para personas celíacas)
- Relevamientos (inspecciones técnicas)
- Rendición de cuentas (mensual y final)

---

## Módulos del Sistema

A continuación se detallan cada uno de los módulos que conforman SISOC. Cada uno cumple una función específica y está diseñado para resolver necesidades particulares del ecosistema de programas sociales.

---

### 1. Comedores

**Propósito:** Administrar los espacios donde se prepara y distribuye la comida.

**Funcionalidades:**
- Registro de comedores con datos de ubicación (dirección, provincia, localidad)
- Gestión del estado operativo (activo, inactivo, en proceso de alta, etc.)
- Sincronización automática con el sistema externo GESTIONAR
- Vinculación con la organización responsable
- Control de capacidad y turnos
- Historial de cambios de estado

**¿Por qué es independiente?** Porque un comedor puede cambiar de organización responsable, y cada uno tiene su propio ciclo de vida operativo independiente de las admisiones.

---

### 2. Organizaciones

**Propósito:** Gestionar las entidades jurídicas que operan los comedores.

**Funcionalidades:**
- Registro de organizaciones (ONGs, iglesias, asociaciones civiles)
- Datos de personería jurídica (número de resolución, fecha de otorgamiento)
- Contactos y responsables legales
- Historial de convenios firmados
- Vinculación con los comedores que operan

**¿Por qué es independiente?** Porque una organización puede tener múltiples comedores bajo su órbita, y la documentación legal se comparte entre todos ellos.

---

### 3. Admisiones

**Propósito:** Gestionar el proceso de incorporación de beneficiarios a los programas.

**Funcionalidades:**
- Creación de expedientes de admisión
- Carga de documentación requerida por tipo de programa
- Flujo de validación (técnico → área legal → aprobación)
- Estados: pendiente, en revisión, rectificar, aceptado
- Historial de observaciones y comentarios
- Vinculación con el ciudadano beneficiario

**¿Por qué es independiente?** Porque cada admisión es un proceso administrativo único que genera documentación específica del evento (no reusable en otros procesos).

---

### 4. Ciudadanos

**Propósito:** Registrar y mantener los datos de los beneficiarios.

**Funcionalidades:**
- Registro de datos personales (nombre, apellido, DNI, fecha de nacimiento)
- Consulta de datos con RENAPER (validación de identidad)
- Historial de programas asociados
- Seguimiento de situación social
- Gestión de grupos familiares

**¿Por qué es independiente?** Porque un ciudadano puede participar en múltiples programas a lo largo del tiempo, y su registro centralizado evita duplicaciones.

---

### 5. Centro de Familia

**Propósito:** Administrar los centros de familia y sus beneficiarios.

**Funcionalidades:**
- Registro de centros de familia
- Gestión de cupos y capacidad
- Admisión de familias al programa
- Seguimiento de acompañamientos
- API para integración con otros sistemas

**¿Por qué es independiente?** Es un programa con lógica distinta a los comedores (modalidad familiar vs. modalidad comunitaria).

---

### 6. Centro de Infancia (CDI)

**Propósito:** Gestionar los centros de infancia y su documentación específica.

**Funcionalidades:**
- Registro de centros de infancia
- Formularios específicos del programa (formulario CDI)
- Datos de infraestructura y capacidad
- Documentación pedagógica y de seguridad
- Seguimiento de niños atendidos

**¿Por qué es independiente?** Tiene requisitos documentales y operativos distintos a los comedores (infraestructura educativa, permisos sanitarios específicos).

---

### 7. Celiaquía

**Propósito:** Administrar el programa de asistencia a personas con celiaquía.

**Funcionalidades:**
- Registro de beneficiarios con diagnóstico de celiaquía
- Gestión de ayuda alimentaria específica (productos sin gluten)
- Seguimiento de tratamientos
- Validación de documentación médica

**¿Por qué es independiente?** Programa específico con requisitos nutricionales y médicos propios, diferente a los programas de comedores.

---

### 8. Relevamientos

**Propósito:** Registrar las inspecciones técnicas de los comedores.

**Funcionalidades:**
- Carga de resultados de inspecciones in situ
- Datos de infraestructura, higiene, seguridad
- Fotos y evidencia documental
- Sincronización con GESTIONAR
- Historial de inspecciones por comedor

**¿Por qué es independiente?** Cada relevamiento es un evento temporal que documenta el estado del comedor en un momento dado (no se modifica, solo se agrega uno nuevo).

---

### 9. Duplas Técnicas

**Propósito:** Gestionar los equipos técnicos territoriales.

**Funcionalidades:**
- Registro de técnicos y coordinadores
- Asignación de territorios (provincias, localidades)
- Vinculación con comedores asignados
- Historial de intervenciones

**¿Por qué es independiente?** Los técnicos son recursos humanos que pueden rotar entre comedores, y su gestión es independiente de los espacios físicos.

---

### 10. Acompañamientos

**Propósito:** Hacer seguimiento de casos específicos de beneficiarios.

**Funcionalidades:**
- Registro de acompañamientos realizados
- Notas de evolución y observaciones
- Vinculación con admisiones y ciudadanos
- Historial de intervenciones

**¿Por qué es independiente?** Es un módulo de seguimiento longitudinal que no depende de un programa específico.

---

### 11. Intervenciones

**Propósito:** Registrar intervenciones especiales sobre casos.

**Funcionalidades:**
- Documentación de intervenciones específicas
- Tipos de intervención configurables
- Vinculación con múltiples entidades (ciudadanos, comedores, organizaciones)

**¿Por qué es independiente?** Las intervenciones pueden originarse desde diferentes módulos y necesitan un registro centralizado.

---

### 12. Expedientes de Pagos

**Propósito:** Gestionar la rendición de cuentas de las organizaciones.

**Funcionalidades:**
- Carga de comprobantes de gasto
- Validación de rendiciones
- Estados de aprobación (pendiente, aprobado, rechazado)
- Historial de liquidaciones

**¿Por qué es independiente?** Proceso financiero separado de la gestión operativa de comedores y admisiones.

---

### 13. Rendición de Cuentas (Mensual y Final)

**Propósito:** Controlar la rendición financiera de las organizaciones.

**Funcionalidades:**
- Rendición mensual de gastos
- Rendición final de cuentas
- Validación contable
- Comparación con presupuesto aprobado

**¿Por qué es independiente?** Proceso contable con flujos y validaciones propias, diferente a la gestión operativa.

---

### 14. Dashboard

**Propósito:** Proporcionar tableros de visualización y estadísticas.

**Funcionalidades:**
- Métricas globales de programas
- Gráficos de evolución
- Indicadores clave (KPI)
- Filtros por período, territorio, programa

**¿Por qué es independiente?** Consume datos de todos los módulos para presentar información consolidada.

---

### 15. Audittrail

**Propósito:** Garantizar trazabilidad y transparencia en el sistema.

**Funcionalidades:**
- Registro de todos los cambios en el sistema
- Identificación de usuario, fecha, hora
- Registro del estado anterior y nuevo
- Consulta de historial por entidad

**¿Por qué es independiente?** Es un módulo transversal que intercepta operaciones de todos los demás módulos.

---

### 16. Users (Gestión de Usuarios)

**Propósito:** Administrar el acceso al sistema.

**Funcionalidades:**
- Creación y gestión de usuarios
- Grupos y permisos (roles)
- Autenticación y sesión
- Restricción por permisos

**¿Por qué es independiente?** Gestión de seguridad y acceso independiente de la lógica de negocio.

---

## ¿Qué tecnología usa?

| Componente | Tecnología |
|------------|------------|
| **Backend** | Django (framework Python) |
| **Base de datos** | MySQL |
| **Contenedores** | Docker + Docker Compose |
| **Frontend** | HTML, CSS, JavaScript, Bootstrap |
| **API** | DRF (Django REST Framework) |
| **Documentación API** | Swagger / Redoc |
| **Testing** | pytest |
| **Monitoreo** | Sentry |

---

## ¿Quiénes lo usan?

| Rol | Función en el sistema |
|-----|----------------------|
| **Equipos técnicos territoriales** | Carga inicial de documentación, relevamientos |
| **Área legal** | Validación de documentación, informes técnico-jurídicos |
| **Administrativos** | Gestión de admisiones, reportes, rendiciones |
| **Coordinadores** | Supervisión de equipos y programas |
| **Contables** | Validación de rendiciones de cuentas |

---

## Resumen ejecutivo

| Aspecto | Descripción |
|---------|-------------|
| **Nombre** | SISOC - Sistema de Información y Seguimiento de Organizaciones y Comedores |
| **Desarrollador** | Gobierno de la Provincia de Buenos Aires - Ministerio de Desarrollo de la Comunidad |
| **Tecnología** | Django + MySQL + Docker |
| **Cantidad de módulos** | 16 módulos funcionales |
| **Usuarios** | Equipos técnicos, área legal, administrativos, coordinadores, contables |
| **Función principal** | Gestionar programas de asistencia alimentaria (comedores, organizaciones, beneficiarios) |
| **Programas** | Alimentar Comunidad, Centro de Familia, Centro de Infancia, Celiaquía |
| **Año de inicio** | 2023 (aproximado) |

---

*Documento generado para presentación institucional - Abril 2026*