# CHANGELOG
Todas las versiones desplegadas deberan estar aca con su descripcion de cambios. Ordenar de mas a menos reciente,

## Tag: `freeze-2025.08.18-2` - Despliegue: 2025.08.20
## Added
- Biblioteca de componentes reutilizables para formularios, tablas y flujos de usuario  
  (mejora la consistencia y rapidez al usar formularios y pantallas nuevas)  
- Estilos y scripts personalizados en frontend  
  (diseño más moderno y experiencia de uso más fluida)  
- Servicios backend para reprocesamiento e informes de Cabal  
  (reportes más rápidos y confiables para gestión interna)  
- Migraciones para modelos de CDI y Centros de Familia  
  (nueva estructura de datos que permite ampliar funcionalidades en esos módulos)  
- Tests ampliados en `comedores` y `relevamientos`  
  (más garantías de calidad y menos riesgo de errores futuros)  

### Changed
- Refactors en servicios de admisiones, CDI, comedores e historial  
  (procesos más estables y con menos errores en la operación diaria)  
- Vistas y plantillas de Centros de Familia reorganizadas y simplificadas  
  (pantallas más claras y navegación más sencilla para usuarios)  
- Configuración de proyecto ajustada (deps, settings, lint, docs)  
  (ajustes internos para mayor estabilidad y facilidad de mantenimiento)  

### Removed
- Servicio legado `informescabal.py`  
  (se reemplaza por un sistema más moderno y confiable de reportes)  
- Plantillas obsoletas de expedientes  
  (pantallas antiguas eliminadas para evitar confusión)  
