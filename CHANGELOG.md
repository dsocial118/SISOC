<!-- AUTO-GENERATED RELEASE START: 2026-04-09 -->
# Versión SISOC 09.04.2026

## Nuevas Funcionalidades

- El envío masivo de credenciales pasó a procesamiento en segundo plano con jobs reanudables y un worker dedicado en producción, evitando depender del tiempo total de una request web.
- VAT centralizó el alta de cursos en un modal con selector asistido de planes curriculares y sumó acciones rápidas en popup para editar o eliminar comisiones desde la misma pantalla.

## Actualizaciones

- El despliegue productivo incorpora compose específico para el worker de credenciales, mientras el entorno local mantiene un stack mínimo y la documentación deja registrado el nuevo flujo operativo.
- La experiencia VAT/INET se ajustó con branding específico en inicio, mejoras en el panel y modal de cursos y documentación funcional actualizada de la API operativa.

## Corrección de Errores

- La búsqueda de ciudadanos por documento pasó a filtros numéricos indexables, reduciendo latencia en alta rápida y nóminas que consultan por DNI.
- Se corrigieron el alta de horarios y el detalle de comisiones de curso, además de warnings MySQL en web push, checks del flujo de credenciales y literales con encoding incorrecto en `custom_filters`.

<!-- AUTO-GENERATED RELEASE END: 2026-04-09 -->

<!-- AUTO-GENERATED RELEASE START: 2026-04-08 -->
# Versión SISOC 08.04.2026

## Nuevas Funcionalidades

- Nuevo flujo de credenciales masivas con variante INET, selector de tipo de envío, plantillas diferenciadas y soporte de lotes grandes desde Usuarios.
- VAT incorporó filtros más ricos en el panel de cursos del centro, popups para acciones rápidas de comisiones y nuevos filtros geográficos en su API operativa.
- El despliegue suma compose versionado por entorno y documentación de homologación para separar configuración de desarrollo, homologación y producción.

## Actualizaciones

- Se reorganizó el menú principal y se ajustó el flujo de rendiciones entre PWA y web, junto con mejoras de paginación, columnas y búsqueda de referentes en centros VAT.
- Se amplió la documentación funcional de la API operativa VAT y se reforzaron regresiones en VAT, PWA, CSP, sidebar y legajos para sostener los cambios recientes.

## Corrección de Errores

- El envío masivo de credenciales ahora corta lotes antes del timeout web, reintenta timeouts SMTP y mejora la validación de correo sin derribar toda la corrida.
- Se corrigieron regresiones en paneles VAT, push subscriptions/PWA, post-importación de Celiaquía y textos mojibake en archivos de homologación.

<!-- AUTO-GENERATED RELEASE END: 2026-04-08 -->

<!-- AUTO-GENERATED RELEASE START: 2026-04-06 -->
# Versión SISOC 06.04.2026

## Nuevas Funcionalidades

- El detalle de centros VAT ahora carga en diferido la solapa de cursos y permite filtrar y paginar planes curriculares y vouchers desde vistas parciales más livianas.

## Actualizaciones

- Se optimizó el rendimiento del detalle de centros VAT con queries más acotadas, cache paginada e índice compuesto para planes curriculares.
- Se ajustó la automatización de CI para ejecutar `djlint` sobre templates modificados y dejar de sobrescribir `CHANGELOG.md`, manteniendo los artefactos spec-as-source y la documentación operativa del corte.

## Corrección de Errores

- Se corrigieron validaciones y nonce CSP del login web, el orden de doble rol en importaciones de Celiaquía y mensajes/links de búsqueda y paginación en VAT.
- Se restauró el estilo del badge judicializado en el detalle de comedores y se estabilizaron checks asociados al release.

<!-- AUTO-GENERATED RELEASE END: 2026-04-06 -->

<!-- AUTO-GENERATED RELEASE START: 2026-04-05 -->
# Versión SISOC 05.04.2026

## Nuevas Funcionalidades

- VAT sumó comandos de importación masiva para centros y usuarios CFP, con `dry-run`, normalización de códigos y geografías, y generación controlada de usernames y correos.

## Actualizaciones

- La importación de centros pasó a aplicar updates parciales seguros y el bootstrap VAT incorporó referentes y centros alineados al flujo institucional vigente.

## Corrección de Errores

- Se endurecieron migraciones e importadores VAT para convivir con datos legacy, preservando fechas históricas y evitando colisiones de usernames no CFP.
- Se destrabó la migración de ubicación de comisiones en MySQL cuando existen nulos legacy, manteniendo la exigencia funcional para nuevas altas.

<!-- AUTO-GENERATED RELEASE END: 2026-04-05 -->

<!-- AUTO-GENERATED RELEASE START: 2026-04-04 -->
# Versión SISOC 04.04.2026

## Nuevas Funcionalidades

- VAT unificó contactos institucionales en alta y edición de centros, eliminando el modelo separado de autoridades y concentrando toda la carga institucional en una sola grilla.
- Los planes curriculares ahora exigen nombre persistido y las comisiones de curso generan automáticamente su código y nombre, con normativa y clasificación académica más consistentes.

## Actualizaciones

- Los cursos VAT ahora derivan programa desde vouchers y manejan ubicación por comisión, permitiendo una configuración más precisa por sede sin romper compatibilidad con el resto del flujo.
- También entraron ajustes de usuarios, mobile/PWA y rendiciones asociados a revisiones del corte, junto con migraciones complementarias en `users` y `comedores`.

## Corrección de Errores

- Se corrigieron hallazgos de review en la edición segura de centros VAT y se estabilizaron migraciones conflictivas de `users` y el rename de índices de auditoría en `comedores`.
- Se cerraron fixes puntuales en mobile y formularios VAT para conservar estado activo, normalizar contactos y evitar inconsistencias durante altas y ediciones.

<!-- AUTO-GENERATED RELEASE END: 2026-04-04 -->

<!-- AUTO-GENERATED RELEASE START: 2026-04-03 -->
# Versión SISOC 03.04.2026

## Nuevas Funcionalidades

- La edición de centros VAT pasó a reutilizar el formulario completo de alta y el detalle del centro permite crear cursos directamente desde cada plan curricular.

## Actualizaciones

- Se reforzó VAT con validaciones compuestas de normativa, modalidades de cursada más claras y asignación automática de provincia y alcance según el usuario.
- Se preparó la configuración SMTP global para Resend y se ajustaron permisos y grupos VAT para nuevos flujos institucionales.

## Corrección de Errores

- Se corrigieron hallazgos de review en centros y planes curriculares, simplificando renderizados y evitando inconsistencias al editar centros sin provincia explícita.

<!-- AUTO-GENERATED RELEASE END: 2026-04-03 -->

<!-- AUTO-GENERATED RELEASE START: 2026-04-02 -->
# Versión SISOC 02.04.2026

## Nuevas Funcionalidades

- VAT incorporó ABM web para cursos y comisiones, soporte de vouchers en cursos, borrado de títulos, planes y ofertas, y validaciones provinciales más ricas para planes curriculares.
- Swagger y Postman de VAT Web se ampliaron con endpoints y ejemplos alineados al contrato vigente para centros, cursos, inscripciones y filtros relacionados.

## Actualizaciones

- Se alineó el scope de acceso de VAT con roles provinciales, referentes legacy y permisos SSE/CFPINET realmente usados en base.
- Se agregaron fixtures iniciales de modalidades de cursada y se ajustaron formularios, templates y serializers para el nuevo flujo de cursos y comisiones.

## Corrección de Errores

- Se corrigieron migraciones MySQL y checks de CI/lint asociados al corte VAT, evitando fallos de deploy y validación automática en el release.

<!-- AUTO-GENERATED RELEASE END: 2026-04-02 -->

# Versión SISOC 31.03.2026

## Nuevas Funcionalidades

- Evolución funcional de VAT con APIs web documentadas en Swagger para centros, títulos, cursos e inscripciones, rediseño del detalle de centros y comisiones, navegación contextual corregida y mejoras en la gestión de vouchers.
- Nuevo alcance de delegación en Usuarios para definir qué grupos y roles puede asignar cada operador, manteniendo filtros y validaciones por scope en alta y edición.
- Reorganización del módulo Comedores con legajo canonizado, solapa de responsables, soporte de nómina independiente por programa y visualización configurable del estado judicializado.
- Ampliación del módulo Centro de Desarrollo Infantil con nueva nomenclatura, formularios y validaciones renovadas, departamentos IPI, teléfonos más flexibles, nuevos campos de funcionamiento/ubicación y una ficha de nómina mucho más completa.

## Actualizaciones

- Unificación de flujos entre web y mobile/PWA para login y colaboradores, con acciones por usuario alineadas al estado activo y mejor consistencia en altas, bajas lógicas y permisos.
- Refinamiento continuo de CDI con resaltado correcto de errores en edición, colores y jerarquías visuales más claros en formularios, y nuevas métricas visibles para género X en detalle y nómina.
- Fortalecimiento del trabajo asistido y la operación técnica con bootstrap para worktrees, checks de mojibake, ajustes de GitHub Actions y guías IA/lint más estrictas en la documentación.
- Mejoras transversales en layout y experiencia de uso en detalle de comedores, sidebar, relevamientos, usuarios y formularios CDI para sostener compatibilidad con los cambios recientes.

## Corrección de Errores

- Correcciones acumuladas en Celiaquía para importación y reproceso de legajos: validación integral de Excel, obligatoriedad de responsables según edad, guardado parcial estable, limpieza del responsable al borrar el último dato y ajustes RENAPER.
- Ajustes en Comedores y Ciudadanos para evitar timeouts por búsqueda de documento, cortar reintentos RENAPER ante errores de integración, restaurar el layout del detalle y corregir regresiones de alcance, tests y migraciones.
- Estabilización de CI, encoding y suites automáticas con fixes de GitHub Actions, normalización UTF-8/mojibake, compatibilidad de migraciones y cobertura de regresión en Users, VAT, CDI, Comedores y PWA.
- Correcciones puntuales en Users y VAT para preservar contraseña temporal, respetar scope parcial de delegación, alinear seeds de grupos y resolver scripts inline bajo CSP y formularios del admin.
<!-- AUTO-GENERATED RELEASE END: 2026-03-31 -->

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
