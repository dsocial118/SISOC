# CHANGELOG
Todas las versiones desplegadas deberan estar aca con su descripcion de cambios. Ordenar de mas a menos reciente,

## Despliegue: 2026.02.03
### Added
- Preferencias de columnas por usuario/listado con endpoint dedicado, modal de configuración en tablas y persistencia en `PreferenciaColumnas`.
- Exportación CSV en listados principales (comedores, usuarios/grupos, ciudadanos, CDI, organizaciones, duplas y acompañamientos) con helper frontend y permisos.
- Pantalla “Novedades del Sistema” que muestra el `CHANGELOG.md`, con cache y fallback a GitHub configurable vía `CHANGELOG_GITHUB_URL`.
- Celiaquía: nuevos modelos para documentos y comentarios (DocumentoLegajo, HistorialComentarios, TipoDocumento) y comando para migrar comentarios históricos.
- Celiaquía: exportación de padrón final en Excel y reporter de provincias con filtros por expediente/documento/estado.
- Documentación y colecciones Postman para APIs, además de guías de migración/validación de Celiaquía.

### Changed
- Detalle nuevo de comedores: layout, modales y observaciones reorganizados; ajustes visuales en barras etarias y componentes.
- Importación Celiaquía: validaciones más estrictas de documentos y edad del responsable, gestión de rol y servicios refactorizados.
- Tablas reutilizables: layout centrado por defecto, paginación/headers actualizados y soporte de configuración de columnas.
- Expedientes de pago: nuevos campos de montos/prestaciones mensuales y renombre de expediente de convenio en formularios.
- Reporter Provincias y grids de admisiones/usuarios con estilos y alineación refinados.

### Fixed
- Orden y badges de estados en nóminas, fecha en detalle de comedor nuevo y línea de tiempo.
- Orden de intervenciones y botones en comedores; eliminación de acciones obsoletas (imprimir).
- Scroll horizontal y layout en listados; correcciones menores de UI/lint/tests.
- Fix de seguridad por alerta de code scanning (DOM text reinterpreted as HTML) y errores de importación.

## Despliegue: 2026.01.23
### Added
- Nueva utilidad `validar_comedores_csv` en `comedores.management.commands` para validar/activar lotes de comedores vía CSV, con validación de entradas, dry-run y registro histórico de cambios.
- Middleware de Content Security Policy con cobertura de scripts, estilos y orígenes externos clave (Maps, DataTables, Power BI) y flag `ENABLE_CSP` para activar el control por entorno.

### Changed
- Fortalecimiento de seguridad en `config/settings.py`: HSTS de 30 minutos sin preload, cookies `HttpOnly`/`SameSite=None` para compatibilidad cross-site y cabeceras anti-sniffing/XSS, manteniendo `ENABLE_CSP`.
- Vistas y servicios de Admisiones/Legales ahora incluyen la columna `N° Convenio` (formato ordinal) y la validación nacional se trata como campo opcional en `InformeTecnicoJuridicoForm`.
- Plantillas PDF/Word de informes técnicos jurídicos refinan la redacción de la organización solicitante, eliminando la repetición del subtipo de entidad.

## Despliegue: 2026.01.21
### Added
- Filtros avanzados favoritos por sección (comedores, admisiones, CDF, duplas, usuarios) con UI de guardado y aplicación.
- Módulo de importación de expedientes de pago con carga, tracking de errores/exitos, delimitador configurable y pantallas dedicadas.
- Endpoints API de Provincias/Municipios/Localidades para Centro de Familia y búsquedas geográficas.
- Tableros administrables desde base (modelo `Tablero`, fixtures y vista dinámica por slug).

### Changed
- Filtros avanzados reordenados con headers por fila y estilos actualizados en la barra de búsqueda.
- Comedores: detalle y nómina renovados (incluye rango etario) y búsqueda en mapa por geolocalización.
- Admisiones/Legales: validaciones de carga, deduplicación en listados, historial de estados y ajustes de estado legal.
- UI renovada en organizaciones, intervenciones y ciudadanos (Historia Social Digital).

### Fixed
- Correcciones de geolocalización en mapas, overflow de select2 y fecha de validación al actualizar comedores.

## Despliegue: 2026.01.02
### Added
- Filtros avanzados combinables para los listados de Admisiones (equipos técnicos y Legales), con configuración de campos/opciones desde backend y UI reutilizable en las tablas.
- Campos de georreferenciación, estado civil y origen de dato para ciudadanos, integrados en formularios y vistas.

### Changed
- Detalle de comedores rediseñado con layout modular, nuevo CSS/JS y secciones de información ampliadas.
- Estados de admisión unificados con estado visible automático y lógica de activación/inactivación centralizada.

## Despliegue: 2025.12.18
### Added
- Auditoría con django-auditlog: app `audittrail`, middleware, señales para comedores/organizaciones y vistas de listado/detalle accesibles desde el menú
    (permite trazar altas, cambios y bajas con el usuario actor)
- Tableros DataCalle provinciales con rutas y grupos dedicados
    (desbloquea visualizaciones segmentadas por jurisdicción)
- Ciudadanos enriquecidos: geodatos, estado civil, programas de transferencia, historial mensual e interacciones más API de búsqueda y detalle estilo dashboard
    (centraliza la información y agiliza la gestión de casos)
- Integración RENAPER desde comedores para crear ciudadanos automáticamente normalizando dirección y nacionalidad (fixtures de nacionalidades incluidas)
    (reduce carga manual y mejora la calidad de datos)
- Documentación reorganizada con índice en `docs/indice.md` y nuevas guías de arquitectura/operaciones/flows
    (mejora la referencia técnica y operativa)
### Changed
- Tabla y estilos de comedores modernizados con badges, sorting y acciones claras; nuevos CSS/JS de listas
    (mejora la usabilidad en búsqueda y gestión)
- Configuración ajustada: enums más legibles en Swagger, nueva env `GOOGLE_MAPS_API_KEY`, filtros choice y grupos creados para los nuevos tableros
    (prepara la plataforma para las nuevas funciones y dashboards)
- Sidebar actualizado con acceso a auditoría y tableros provinciales
    (alineado con los nuevos permisos y vistas)
### Removed
- `DEPLOY_WEBP.md`
    (se elimina documentación obsoleta)

## Tag: `2025.09.03-rcX` - Despliegue: 2025.09.03
### Added
- Búsqueda avanzada y módulo de comedores con componentes reutilizables de interfaz
    (permite localizar comedores con filtros específicos y agiliza la gestión)
- Componentes de diseño compartidos y estilos base para todas las vistas
    (unifica la apariencia y facilita el mantenimiento del frontend)
### Changed
- Reestructuración de layouts, navegación y tablas para vista unificada en todo el sistema
    (simplifica el desarrollo de nuevas pantallas y mejora la experiencia de uso)

## Tag: `2025.08.18-rc2` - Despliegue: 2025.08.20
### Added
- Biblioteca de componentes reutilizables para formularios, tablas y flujos de usuario 
    (facilita armar pantallas de manera rápida y uniforme)
- Estilos y scripts personalizados en frontend 
    (mejoran la apariencia y la interacción visual)
- Servicios backend para reprocesamiento e informes de Cabal 
    (permiten volver a generar y consultar reportes automáticamente)
- Migraciones para modelos de CDI y Centros de Familia 
    (preparan la base de datos para nuevas funciones en estas áreas)
- Tests ampliados en comedores y relevamientos 
    (aumenta la confianza de que todo funciona correctamente)
### Changed
- Refactors en servicios de admisiones, CDI, comedores e historial 
    (hace el desarrollo más eficiente y ordenado)
- Vistas y plantillas de Centros de Familia reorganizadas y simplificadas 
    (las pantallas son más claras y fáciles de usar)
- Configuración de proyecto ajustada (dependencias, settings, lint, docs) 
    (el sistema está mejor configurado y documentado)
### Removed
- Servicio legado informescabal.py 
    (se eliminó un servicio antiguo que ya no se utiliza)
- Plantillas obsoletas de expedientes 
    (se quitaron diseños viejos que ya no se usan)
