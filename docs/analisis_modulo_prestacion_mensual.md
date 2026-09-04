# Análisis Funcional del Nuevo Módulo: Programa de Prestación Mensual

## Introducción

Este documento presenta un análisis funcional del nuevo módulo propuesto para el sistema SISOC (Sistema de Información Social y Organizacional). El módulo se centra en la gestión de un programa de prestación mensual con monto plano, incorporando procesos de nómina, documentación por persona y validaciones externas. El análisis se realiza a nivel funcional, enfocándose en procesos, roles, flujos de trabajo y requisitos de negocio, sin entrar en detalles técnicos de implementación.

El objetivo es comprender el flujo operativo completo, identificar roles clave, definir etapas críticas y proponer consideraciones para la integración con el ecosistema existente de SISOC, que incluye módulos como ciudadanos, admisiones y audittrail.

## Descripción General del Módulo

El módulo gestiona un programa de prestaciones sociales mensuales donde cada beneficiario recibe un monto fijo. El proceso se basa en nóminas dinámicas que evolucionan mensualmente, con validaciones externas (RENAPER y ANSES) y documentación adjunta. La clave es mantener la integridad de los datos ciudadanos (historias sociales digitales) y registrar todas las acciones para auditoría.

Características principales:
- **Nómina inicial**: Base de datos de beneficiarios y responsables cargada externamente.
- **Validaciones**: Cruce con RENAPER para verificación de identidad.
- **Documentación**: Adjuntos requeridos por grupo familiar (beneficiario + responsable).
- **Ciclos mensuales**: Generación, derivación, revisión y consolidación de nóminas.
- **Auditoría**: Registro inmutable de todas las versiones y acciones.
- **Reactivaciones**: Optimización para personas ya registradas en el sistema.

## Roles y Responsabilidades

Para el correcto funcionamiento del módulo, se identifican los siguientes roles funcionales:

1. **Usuario Provincial**:
   - Carga la nómina inicial en Excel.
   - Adjunta documentación por grupo familiar.
   - Solicita y genera nóminas mensuales.
   - Consolida nómina final considerando comentarios de ANSES.
   - Gestiona bajas y altas en la nómina inicial.

2. **Sistema SISOC (Automatizado)**:
   - Integra personas a legajos ciudadanos.
   - Realiza cruces con RENAPER.
   - Genera documentos exportables (Excel, PDF de derivación, DDJJ).
   - Registra acciones para auditoría.
   - Maneja el cierre de períodos.

3. **Operador del Gobierno Nacional**:
   - Ingresa comentarios de ANSES por persona en la nómina provincial.
   - Determina la continuidad de beneficiarios basada en retroalimentación externa.

4. **ANSES (Externo)**:
   - Recibe la nómina derivada.
   - Proporciona comentarios por persona (no integrado directamente en SISOC).

Estos roles interactúan en un flujo secuencial, con SISOC actuando como puente entre la provincia, el gobierno nacional y entidades externas.

## Flujo de Trabajo Detallado

El flujo se divide en fases: inicialización, ciclo mensual y cierre/auditoría. A continuación, se detalla paso a paso.

### Fase 1: Inicialización del Programa
1. **Carga de Nómina Inicial**:
   - El usuario provincial sube un archivo Excel con beneficiarios y responsables.
   - Estructura de datos: Proporcionada externamente (no definida por SISOC), incluye campos como nombres, DNI, relaciones familiares, etc.
   - Acción: SISOC procesa el archivo y crea legajos ciudadanos para cada persona nueva.

2. **Integración de Personas**:
   - Cada persona se registra en el sistema como legajo ciudadano (historia social digital).
   - Para nuevos: Se abre un legajo completo.
   - Para existentes (reactivaciones): Se reutiliza el legajo sin recargar datos básicos.

3. **Validación con RENAPER**:
   - Por cada persona, se realiza un cruce automático con RENAPER.
   - Los datos deben ser contrastados manualmente por el usuario provincial (e.g., verificar coincidencias en nombre, fecha de nacimiento).
   - Si hay discrepancias, se requiere corrección o documentación adicional.

4. **Adjunto de Documentación**:
   - Por cada grupo (beneficiario + responsable), se adjuntan documentos requeridos (tipo y formato pendientes de definición externa).
   - Esto consolida la "primera versión" de la nómina inicial.

5. **Consolidación Inicial**:
   - La nómina inicial queda lista como base para meses futuros.
   - Solo permite modificaciones por bajas/altas; no se recarga personas ya integradas.

### Fase 2: Ciclo Mensual (Aproximadamente el Día 20)
1. **Solicitud de Nómina Mensual**:
   - El usuario provincial indica la necesidad de generar una nómina para el período actual.
   - SISOC arma la nómina basada en la inicial, aplicando cualquier baja/alta reciente.

2. **Generación de Documentos**:
   - Exporta la nómina en Excel.
   - Genera un documento de derivación (PDF, modelo pendiente).
   - Crea una declaración jurada (DDJJ) en PDF, que requiere formularios completados por la provincia.

3. **Derivación a ANSES**:
   - La nómina se envía externamente a ANSES para revisión.
   - ANSES analiza y deja comentarios por persona (e.g., aprobaciones, rechazos, observaciones).

4. **Ingreso de Comentarios por Operador Nacional**:
   - El operador del gobierno nacional accede a la nómina provincial en SISOC.
   - Ingresa los comentarios de ANSES por cada persona.
   - Esto determina si el beneficiario continúa o no.

5. **Habilitación de Nómina a Provincia**:
   - La nómina se devuelve a la provincia con comentarios incorporados.

6. **Consolidación de Nómina Final**:
   - El usuario provincial revisa comentarios y consolida la versión final.
   - Ajustes basados en retroalimentación (e.g., excluir personas rechazadas).

7. **Descarga y Envío Final**:
   - Se descarga la nómina final en Excel, junto con DDJJ actualizada.
   - Envío externo para procesamiento de pagos.

### Fase 3: Cierre de Período y Auditoría
1. **Cierre en SISOC**:
   - Se cierra el período mensual.
   - Registro inmutable: Nómina inicial, comentarios de ANSES, nómina final, documentos de derivación, acciones por usuario.

2. **Preparación para el Siguiente Mes**:
   - La nómina inicial se conforma automáticamente con la nómina de pago del mes anterior.
   - Para reactivaciones: Si la persona ya existe, se omite validación con RENAPER.

## Consideraciones Funcionales

- **Integración con Módulos Existentes**:
  - **Ciudadanos**: Uso de legajos para historias sociales digitales.
  - **Audittrail**: Registro de todas las acciones para trazabilidad.
  - **Admisiones**: Posible alineación con procesos de ingreso de beneficiarios.

- **Gestión de Cambios**:
  - La nómina inicial es semi-estática: Solo bajas/altas permitidas para evitar recargas innecesarias.
  - Reactivaciones optimizan el flujo al reutilizar datos existentes.

- **Validaciones Externas**:
  - RENAPER: Obligatorio para nuevos; opcional para reactivaciones.
  - ANSES: Comentarios críticos para la aprobación final.

- **Documentación y Formularios**:
  - Modelos de derivación y DDJJ pendientes; requieren integración de formularios provinciales.
  - Adjuntos por grupo: Flexibles, pero deben ser obligatorios para consolidación.

- **Ciclos y Temporalidad**:
  - Mensual fijo (día 20 aprox.), pero adaptable.
  - Cierre de período impide ediciones posteriores.

- **Riesgos Funcionales**:
  - Dependencia de datos externos (Excel, RENAPER, ANSES).
  - Necesidad de coordinación entre provincia y nacional.
  - Volumen de datos: Escalabilidad para nóminas grandes.

## Conclusiones y Próximos Pasos

Este módulo fortalece SISOC al centralizar la gestión de prestaciones mensuales, promoviendo eficiencia (evitando recargas) y auditoría completa. El flujo es lineal pero flexible, con puntos de validación clave para asegurar calidad de datos.

Próximos pasos recomendados:
- Definir estructuras de datos externas (nómina Excel, modelos de PDF).
- Validar integración con módulos existentes (e.g., ciudadanos para legajos).
- Prototipar flujos con usuarios provinciales y nacionales para refinar roles.
- Estimar impacto en carga de trabajo y proponer métricas de éxito (e.g., tiempo de procesamiento por nómina).

Este análisis funcional sirve como base para el diseño técnico y la implementación. Si se requieren ajustes o expansiones, se puede iterar basado en feedback adicional.