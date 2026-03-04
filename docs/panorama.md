# Overview

## 1) Qué es el sistema
- Backoffice Django para SISOC que centraliza módulos de comedores, centro de familia, relevamientos y ciudadanía. Evidencia: README.md:1-4; config/settings.py:42-83; config/urls.py:12-44.
- API documentada con drf-spectacular (Swagger/Redoc) y front servidor de plantillas; expone `/api/docs` y `/api/redoc`. Evidencia: config/settings.py:195-234; config/urls.py:35-43.
- Desplegable vía Docker Compose (servicios mysql y django) con setup automatizado de migraciones/fixtures en el entrypoint. Evidencia: docker-compose.yml:1-34; docker/django/entrypoint.py:55-95.
- Variables de entorno parametrizan DB y claves externas (GESTIONAR/RENAPER), más puertos y dominio. Evidencia: .env.example:1-51; config/settings.py:153-241.

## 2) Qué NO es / fuera de alcance
- Gestión con usuarios externos a organismos gubernamentales.
- No se declara procesamiento de pagos ni portal público ciudadano.

## 3) Actores y permisos (alto nivel)
- Grupos de usuario predefinidos incluyen Admin, Comedores (listar/crear/ver/editar/eliminar), roles de técnico/comedor/coordinador, algunos data entry, áreas legales/contable, dashboards de datos, roles celiaquía y API CentroFamilia. Evidencia: users/management/commands/create_groups.py:1-61.
- Usuarios de prueba en DEBUG asignan combinaciones de permisos (abogadoqa, tecnicoqa, legalesqa, contableqa, etc.). Evidencia: users/management/commands/create_test_users.py:1-80.
- Otros roles mencionados (técnicos, abogados, representantes provinciales, auditores, datos) sin mapeo directo en código. Evidencia: DESCONOCIDO.

## 4) Casos de uso top 5
- Gestionar comedores (altas, estados, sincronización con GESTIONAR, territoriales). Evidencia: comedores/management/commands/*.py; comedores/tasks.py:1-249; config/urls.py:19-20.
- Registrar y sincronizar relevamientos de comedores con GESTIONAR. Evidencia: relevamientos/management/commands/*.py; relevamientos/tasks.py:1-144; config/urls.py:31-32.
- Administrar ciudadanos, admisiones, centro de familia y celiaquía (formularios/beneficiarios). Evidencia: config/urls.py:21-27,33.
- Operar dashboards y auditoría (dashboard app, audittrail, healthcheck). Evidencia: config/settings.py:64-83; config/urls.py:18,23,27.
- Gestionar usuarios y grupos internos de acceso. Evidencia: users/management/commands/create_groups.py:1-61; config/urls.py:15-16.

## 5) Mapa de apps
| App | Responsabilidad |
| --- | --- |
| users | Autenticación y gestión de usuarios/perfiles. Evidencia: config/settings.py:64; config/urls.py:15-16. |
| core | Utilidades comunes, fixtures, logging. Evidencia: config/settings.py:65; core/management/commands/load_fixtures.py:8-77. |
| dashboard | Tableros internos. Evidencia: config/settings.py:66; config/urls.py:18. |
| comedores | Gestión de comedores, estados, sincronización GESTIONAR. Evidencia: config/settings.py:67; config/urls.py:19-20; comedores/tasks.py:1-249. |
| organizaciones | Módulo de organizaciones vinculadas. Evidencia: config/settings.py:68; config/urls.py:20. |
| centrodeinfancia | Centros de infancia. Evidencia: config/settings.py:69; config/urls.py:21. |
| ciudadanos | Gestión de ciudadanos/beneficiarios. Evidencia: config/settings.py:70; config/urls.py:24. |
| duplas | Gestión de duplas técnicas. Evidencia: config/settings.py:71; config/urls.py:22. |
| admisiones | Procesos de admisión. Evidencia: config/settings.py:72; config/urls.py:25. |
| intervenciones | Intervenciones sobre casos. Evidencia: config/settings.py:73. |
| historial | Historial de cambios. Evidencia: config/settings.py:74. |
| acompanamientos | Seguimiento y acompañamientos. Evidencia: config/settings.py:75; config/urls.py:28. |
| expedientespagos | Expedientes de pagos. Evidencia: config/settings.py:76; config/urls.py:29. |
| relevamientos | Relevamientos de comedores. Evidencia: config/settings.py:77; config/urls.py:31-32. |
| rendicioncuentasfinal | Rendición final de cuentas. Evidencia: config/settings.py:78; config/urls.py:30. |
| rendicioncuentasmensual | Rendición mensual. Evidencia: config/settings.py:79; config/urls.py:32. |
| centrodefamilia | Gestión de centros de familia y beneficiarios. Evidencia: config/settings.py:80; config/urls.py:26,35. |
| celiaquia | Módulo celiaquía. Evidencia: config/settings.py:81; config/urls.py:33. |
| audittrail | Auditoría y purga de logs. Evidencia: config/settings.py:82; config/urls.py:23. |
| healthcheck | Endpoint de salud. Evidencia: config/urls.py:27; healthcheck/urls.py:1-5. |

## 6) Integraciones externas
- MySQL como base de datos principal. Evidencia: config/settings.py:153-168; docker-compose.yml:1-19.
- GESTIONAR (API) para sincronizar comedores, referentes, observaciones y relevamientos (con threads y `requests`). Evidencia: comedores/tasks.py:11-249; relevamientos/tasks.py:13-144; config/settings.py:236-241.
- RENAPER para consulta de datos de ciudadanos con token cacheado. Evidencia: centrodefamilia/services/consulta_renaper.py:13-170; config/settings.py:236-241.
- Google Maps API key opcional. Evidencia: config/settings.py:241.

## 7) Riesgos y supuestos
- Dependencia fuerte de variables de entorno (DB, GESTIONAR, RENAPER, DOMINIO); ausencia puede romper arranque. Evidencia: .env.example:1-51; config/settings.py:153-241.
- Sin colas dedicadas: sincronizaciones externas usan hilos; riesgo de timeouts/bloqueos en procesos web si no se gestionan errores. Evidencia: comedores/tasks.py:1-249; relevamientos/tasks.py:1-144.
- Entrypoint ejecuta `makemigrations` en arranque de contenedor, con posible modificación de esquema en runtime si hay modelos nuevos. Evidencia: docker/django/entrypoint.py:55-65.
- Cache in-memory (LocMem) no es compartida entre instancias; suposiciones de cache podrían no escalar en múltiples réplicas. Evidencia: config/settings.py:175-189.

## TODOs
- Confirmar actores reales y su mapeo a grupos/permissions más allá de los grupos predefinidos.
- Validar y documentar explícitamente qué queda fuera de alcance (portal ciudadano, pagos, etc.).
