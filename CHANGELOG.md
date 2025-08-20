# CHANGELOG
Todas las versiones desplegadas deberan estar aca con su descripcion de cambios. Ordenar de mas a menos reciente,

## freeze-2025.08.18-2
### Adiciones
Biblioteca de componentes reutilizables (templates/components) para formularios, tablas y flujos de usuario
Recursos front-end personalizados: nuevos estilos e imágenes en static/custom/css y scripts interactivos en static/custom/js
Servicios y comandos de backend, destacando los orientados al re-procesamiento e informes de Cabal
Migraciones de datos que introducen y reorganizan modelos relacionados con CDI y Centros de Familia
### Modificaciones
Refactors en múltiples servicios (admisiones, CDI, comedores, historial, rendición de cuentas) que modernizan la lógica de negocio
Vistas y plantillas para Centros de Familia reorganizadas y simplificadas, con nuevas pantallas para informes Cabal
Configuración general del proyecto ajustada: requirements.txt, config/settings.py, flujos de lint y documentación actualizada
### Eliminado
Servicio legado informescabal.py y plantillas obsoletas de expedientes de Centros de Familia
### Tests
Cobertura ampliada con casos adicionales en comedores/tests.py y relevamientos/tests.py

