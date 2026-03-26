<!-- AUTO-GENERATED RELEASE START: 2026-04-01 -->
# Versión SISOC 01.04.2026

## Actualizaciones

- [sin-area] Codex/fix renaper timeout worker exit. (PR #1369)
<!-- AUTO-GENERATED RELEASE END: 2026-04-01 -->

# Versión SISOC 18.03.2026

## Nuevas Funcionalidades

- Nuevo módulo VAT para gestionar centros territoriales, actividades, beneficiarios, responsables y encuentros con servicios, formularios, filtros avanzados, vistas y endpoints API autorizados por roles específicos.
- Evolución profunda del módulo Centro de Infancia: nuevos formularios acordeón, detalle renovado, modelo de trabajadores, vistas CRUD y cobertura de tests para documentación, nominas y permisos.
- Automatización de bootstrap de grupos IAM junto con scripts para generación automática de documentación y changelog/PRs en CI, lo que garantiza que ambientes nuevos migren los permisos correctos.

## Actualizaciones

- Consolidación de GitHub Actions y scripts de CI: nuevos workflows para lint, pruebas, documentación y secretos, plus scripts en `scripts/ci/pr_doc_automation.py` y seeds en `users/bootstrap` para sincronizar entornos con el mismo catálogo de permisos.
- Mejoras de seguridad y permisos (gitleaks allowlist, categorías de filtros booleanos y ajustes en `core.permissions`) que refuerzan el filtrado en Comedores, Ciudadanos, Celiaquía y PWA sin romper compatibilidad.
- Documentación y registros actualizados en `docs/` para explicar decisiones de formularios CDI, pruebas, workflows de CI y despliegue, facilitando trazabilidad de los cambios recientes.

## Corrección de Errores

- Varios ajustes en Celiaquía, Ciudadanos, Comedores y Comunicados (filtros booleanos, rendiciones de listas, permisos de detalle y renderizado de expedientes) que cerraron regresiones reportadas en PRs recientes.
- Limpieza de servicios críticos como auditoría, consulta RENAPER y APIs de PWA para evitar warnings de pylint y mantener los datos sincronizados con los nuevos modelos.
- Estabilización de suites de tests y fixtures (Pytest, GH Actions, cobertura y seeds) que recuperan la compatibilidad tras cambios en formularios, CI y permisos.

# Versión SISOC 04.03.2026

## Nuevas Funcionalidades

- Lanzamiento del nuevo módulo de Comunicados, con mensajes internos y externos, adjuntos, destacados y control de visibilidad por perfil, para una comunicación institucional más ordenada y efectiva.
- Habilitación de API REST para Comunicados externos para la PWA.
- Implementación de una Papelera inteligente, con vista previa de impacto antes de eliminar y capacidad de recuperación, reduciendo riesgos operativos y mejorando el control de cambios.
- Creacion del modulo de Centro de Infancia basico (listo para sumar implementaciones), con flujos para nómina, intervenciones y documentación, y segmentación por provincia para una gestión territorial más precisa.
- Incorporación del ABM de Montos de Prestaciones vinculado a programas, permitiendo administrar valores con mayor trazabilidad y consistencia.
- Evolución del esquema de capacitaciones con nuevas categorías (incluyendo Formando Capital Humano) y subtipos específicos para seguimiento más fino de acciones.

## Actualizaciones

- Gran evolución del módulo de Auditoría con nuevos filtros, exportaciones y metadata persistida, mejorando la lectura de actividad y la toma de decisiones.
- Fortalecimiento de seguridad y confiabilidad con mejoras en políticas CSP y nueva integración de observabilidad con Sentry para detección temprana de incidentes.
- Mejora de rendimiento en procesos críticos mediante optimización de consultas, reducción de sobrecarga en listados y ajustes de índices en base de datos.
- Reorganización de servicios en una arquitectura modular, manteniendo compatibilidad y acelerando mantenimiento futuro.
- Actualización de experiencia visual en pantallas clave (Expedientes de Pago, Centro de Infancia y Novedades), con navegación más clara y foco en productividad diaria.
- Mayor robustez operativa con mejoras de entornos QA/PROD y sincronización de fixtures
- Ampliación de cobertura de pruebas automatizadas a un 75% del codigo critico.

## Corrección de Errores

- Correcciones en validación de archivos y destinatarios en flujos de Admisiones y Comunicados para evitar cargas inconsistentes.
- Ajustes en permisos y reglas de acceso a detalle de comunicados, alineando visibilidad según perfil y contexto.
- Resolución de incidencias de paginación en Papelera para evitar consumo innecesario de memoria.
- Corrección de compatibilidad en nonce CSP y cierre de vulnerabilidades de inyección en vistas de comunicados.
- Ajustes de estabilidad en formularios y modales de intervenciones para evitar inconsistencias de selección.
- Mejoras en parseo de respuestas RENAPER y compatibilidad con borrado lógico en flujos asociados.

# Versión SISOC 18.02.2026

## Nuevas Funcionalidades

- Nuevo flujo de Informe Técnico DOCX en módulo Admisiones, con generación, edición, carga y cierre de informe
- Incorporación de acceso PWA por comedor con autenticación por token y endpoints de sesión para operadores
- Nuevas acciones API para gestión de usuarios y operadores en PWA, incluyendo asignación de comedores
- Incorporación de endpoints para rendiciones de cuenta con detalle, validación, carga de comprobantes y presentación

## Actualizaciones

- Ampliación de estados y reglas de negocio en Admisiones para trazabilidad de informes, subsanaciones y documentación asociada
- Mejora de segmentación en APIs de Comedores para limitar la información según permisos y alcance de acceso PWA
- Reorganización de formularios, vistas y plantillas en módulos Admisiones y Usuarios para consolidar flujos operativos
- Actualización de documentación técnica y de seguridad para backend PWA e inventario de APIs
- Gran ampliación de cobertura de pruebas automáticas (test coverage de 75%), con nuevos casos en módulos críticos y escenarios de integración

## Corrección de Errores

- Refuerzo de redirecciones seguras para prevenir desvíos no confiables en flujos sensibles
- Correcciones de consistencia en validaciones, serialización y respuestas de endpoints
- Ajustes de compatibilidad en configuración y ejecución de pruebas para mejorar estabilidad general

# Versión SISOC 03.02.2026

## Nuevas Funcionalidades

- Personalización de grillas (elección y orden de columnas) por usuario en Módulos Comedores, Admisión - Técnicos, Admisión - Legales, Acompañamiento y Usuarios
- Exportación en CSV de listados en módulos Comedores, Admisión - Técnicos, Admisión - Legales, Acompañamiento y Organizaciones
- Módulo de Novedades del Sistema, con historial de cambios y versiones
- Actualización de modelos para documentación y comentarios en módulo Celiaquía
- Exportación en Excel de nómina final de beneficiarios / responsables en módulo Celiaquía
- Reportes por provincias con filtros personalizables en módulo Celiaquía
- Nueva documentación para APIS y guías de migración

## Actualizaciones

- Nuevo detalle de Comedores, con ajustes visuales y reorganización de elementos
- Mejoras en las validaciones para documentación y edad de responsables en módulo Celiaquía
- Mejoras en visualización y ordenamiento de archivos en módulo de Importación de Expedientes de Pago
- Inclusión de tablas reutilizables, con paginación y encabezamientos actualizados

## Corrección de Errores

- Mayor claridad en nóminas de módulo Comedores, con nuevas etiquetas, fechas de alta y línea de tiempo
- Reordenamiento de elementos en módulo Comedores, con foco en Intervenciones, acciones y eliminación de funciones obsoletas
- Mejoras de visualización en listados para facilitar navegación horizontal
- Correcciones en la seguridad y estabilidad del sistema

# Versión SISOC 23.01.2026

## Nuevas Funcionalidades

- Validación de comedores individual y masiva mediante documento CSV
- Refuerzos en seguridad para la carga de contenidos externos en el sistema

## Actualizaciones

- Mejoras de seguridad para el manejo de conexiones y cookies
- Vista mejorada en las grillas de búsqueda y la información disponible para los módulos de Admisión - Técnicos y Admisión - Legales
- Modificación en campos obligatorios para la realización de Informes Técnicos de Comedores
- Mejoras en plantillas de Informes Técnicos de Comedores

# Versión SISOC 21.01.2026

## Nuevas Funcionalidades

- Incorporación de filtros de búsqueda favoritos por usuario en módulos Comedores, Admisión - Técnicos, Admisión - Legales, Centros de Familia y Usuarios.
- Incorporación de módulo de importación de expedientes de pago
- Incorporación de servicios de ubicación para consulta de Provincias, Municipios y Localidades en módulo Centros de Familia
- Administración de tableros desde el sistema

## Actualizaciones

- Reordenamiento de filtros avanzados con estilos actualizados en módulos Comedores, Admisión - Técnicos y Admisión - Legales
- Detalle de Comedores renovada
- Nomina de Comedores renovada
- Nuevas validaciones y ajustes en Módulo de Admisión - Legales
- Interfaz de usuario renovada para Módulos Organizaciones, Intervenciones e Historia Social Digital

## Corrección de Errores

- Priorización de geolocalización por sobre dirección en mapas
- Vista de la fecha de validación en módulo de Comedores

# Versión SISOC 02.01.2026

## Nuevas Funcionalidades

- Incorporación de filtros avanzados combinables con configuración de campos en los módulos de Admisión - Técnicos y Admisión - Legales
- Nuevos campos de para georreferenciación, estado civil y origen de datos para el módulo de Historia Social Digital

## Actualizaciones

- Nueva vista del Detalle de Comedores
- Unificación de Estados de Admisiones, con automatización y lógica de activación/inactivación centralizada

# Versión SISOC 18.12.2025

## Nuevas Funcionalidades

- Nuevo módulo de Auditoría con registros de creación, edición o eliminación por módulo y por usuario.
- Tableros Data Calle con rutas y grupos definidos, segmentando la vista según la jurisdicción.
- Ampliación de la información disponible en módulo Historia Social Digital: ubicación, estado civil, programas, historial e interacciones
- Integración con RENAPER desde Módulo Comedores para creación de Historia Social Digital normalizada
- Reorganización de documentación del sistema con nuevos índices y guías de funcionamiento

## Actualizaciones

- Grilla de comedores renovada, con nuevas etiquetas, ordenamiento y acciones más claras
- Sidebar actualizado con nuevos accesos a Módulos Auditoría y Tableros por provincia
- Nueva configuración para la integración con mapas y nuevos filtros para mejorar la organización de los datos
- Nuevos grupos disponibles para la implementación de nuevos tableros

Eliminado

- Documentación DEPLOY_WEBP.md obsoleta

# Vresión SISOC 03.09.2025

## Nuevas Funcionalidades

- Inclusión de componentes reutilizables para módulo Comedores
- Búsqueda avanzada en módulo Comedores, con combinación de filtros
- Unificación de todas las vistas del sistema con componentes compartidos y estilos base

## Actualizaciones

- Reestructuración de la distribución de objetos en pantalla y navegación dentro del sistema

# Versión SISOC 20.08.2025

## Nuevas Funcionalidades

- Bibilioteca de componentes reutilizables para nuevos formularios, tablas y flujos de usuario
- Estilos personalizados en la visualización del sistema
- Servicios para reprocesamiento de documentación externas en módulo Centros de Familia
- Test ampliados en módulos Comedores y Relevamientos

## Actualizaciones

- Mejoras en el rendimiento en módulos Admisión - Técnicos, Admisión - Legales, Comedores e Historial
- Simplificación de vista para módulo Centros de Familia
- Configuración y documentación del sistema

Eliminado

- Servicio informescabal.py obsoleto
- Plantillas de expedientes en desuso
