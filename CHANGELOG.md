# CHANGELOG
Todas las versiones desplegadas deberan estar aca con su descripcion de cambios. Ordenar de mas a menos reciente,

## Tag: `2025.09.03-rcX` - Despliegue: 2025.09.03
### Added
- Búsqueda avanzada y módulo de comedores con componentes reutilizables de interfaz
    (permite localizar comedores con filtros específicos y agiliza la gestión)
- Apps de acompañamientos, admisiones, CDI, centro de familia y usuarios con modelos, formularios y vistas iniciales
    (sientan la base funcional del sistema para registrar y administrar datos)
- Migraciones iniciales y plantillas asociadas para cada área
    (preparan la base de datos y la interfaz para operar con los nuevos módulos)
- Pruebas unitarias y datos mock para relevamientos y clasificación de comedores
    (aumenta la cobertura y confiabilidad de los servicios)
- Workflows de CI, configuración de lint y plantillas de issues/PR
    (automatiza revisiones de código y estandariza los procesos de contribución)
- Componentes de diseño compartidos y estilos base para todas las vistas
    (unifica la apariencia y facilita el mantenimiento del frontend)
- Documentación y guías iniciales en README y componentes
    (ofrece referencias claras para desarrolladores y usuarios)
### Changed
- Reestructuración de layouts, navegación y tablas para vista unificada en todo el sistema
    (simplifica el desarrollo de nuevas pantallas y mejora la experiencia de uso)
- Ajustes en modelos y servicios de admisiones y centro de familia
    (permiten gestionar expedientes y reportes con mayor precisión)
- Configuración de proyecto y dependencias actualizada (.env, .pylintrc, settings)
    (mejora la organización del repositorio y su despliegue)
### Removed
- Modelo de expediente legado en centro de familia y vistas asociadas
    (elimina estructuras obsoletas y evita inconsistencias)

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
