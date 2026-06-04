# API Inventory — SISOC

Todas las APIs (internas y externas) están documentadas en la colección única:
**`SISOC APIs.postman_collection.json`** · 167 requests · 11 carpetas · entorno: `Local.postman_environment.json`

---

## Estructura de la colección

| Carpeta | Requests | Descripción |
|---------|----------|-------------|
| Auth | 3 | Login, logout, contexto de usuario (`/api/users/`) |
| Comedores | 10 | CRUD comedores + nómina (`/api/comedores/`) |
| RENAPER | 3 | Historial interno de consultas RENAPER (`/api/renaper/`) |
| Centro de Familia | 21 | CRUD centros, actividades, categorías, participantes, ubicación (`/api/centrodefamilia/`) |
| Comunicados | 7 | CRUD institucional + list/create por comedor (`/api/comunicados/`) |
| Relevamientos | 2 | PATCH relevamiento + primer seguimiento (`/api/relevamiento`) |
| PWA | 33 | Health, push, colaboradores, actividades, formación, mensajes, nómina (`/api/espacios/`) |
| Ticketera | 3 | Alta usuario, verificar auth, cambiar password (`/api/ticketera/`) |
| VAT | 74 | Ver detalle abajo |
| Integraciones Externas | 9 | GESTIONAR (AppSheet) + RENAPER API externa |
| Docs | 2 | OpenAPI schema SISOC + VAT (`/api/schema/`) |

---

## VAT (74 requests)

| Subcarpeta | Requests | Endpoints principales |
|-----------|----------|----------------------|
| Operativo - Planes, Centros, Cursos, Comisiones | 38 | provincias, municipios, planes-curriculares, centros, cursos, comisiones-curso, sectores, subsectores, localidades, modalidades, titulos-referencia, institucion-contactos/identificadores/ubicaciones, ofertas-institucionales, comisiones, comision-horarios, inscripciones, inscripciones-oferta, inscripciones-curso, evaluaciones, resultado-evaluaciones, vouchers, web/ciudadanos |
| Operativo - Cursos Busqueda y Prioritarios | 11 | `vat/cursos/buscar/`, `vat/cursos/prioritarios/` con casos de error |
| Web - Mi Argentina Inscripcion | 6 | `vat/web/cursos/`, `vat/web/ciudadanos/voucher-estado/`, `vat/web/inscripciones/prevalidar/`, `vat/web/inscripciones/` |
| Web - Sectores Subsectores Cursos | 19 | `vat/web/centros/`, `vat/web/titulos/`, `vat/web/cursos/`, `vat/inscripciones-curso/`, `vat/vouchers/por_ciudadano/` |

---

## Integraciones Externas (9 requests)

| Servicio | Acción | Método | Tabla / Endpoint |
|----------|--------|--------|-----------------|
| GESTIONAR (AppSheet) | Find/Crear Comedor | POST | `Comedores` |
| GESTIONAR (AppSheet) | Crear/Eliminar Relevamiento | POST | `RelevamientoComedores` |
| GESTIONAR (AppSheet) | Crear DiasPrestacion | POST | `DiasPrestacion` |
| GESTIONAR (AppSheet) | Crear/Eliminar PrimerSeguimiento | POST | `Seguimientos1erVisita` |
| RENAPER | Login | POST | `/auth/login` |
| RENAPER | Consultar ciudadano por DNI | GET | `/consultarenaper` |

---

## Variables de entorno (`Local.postman_environment.json`)

### SISOC / General

| Variable | Descripción |
|----------|-------------|
| `baseUrl` | URL base SISOC (default: `http://localhost:8000`) |
| `vatBaseUrl` | URL base VAT operativo (default: `http://localhost:8001`) |
| `apiPrefix` | Prefijo REST (default: `/api`) |
| `authToken` | Token sesión Django — formato: `Token <valor>` |
| `apiKey` | Api-Key DRF — formato header: `Api-Key <valor>` |

### IDs de entidades SISOC

| Variable | Entidad |
|----------|---------|
| `centro_id` | CentroFamilia / Centro VAT |
| `actividad_id` | Actividad (Centro de Familia) |
| `comunicado_id` | ComunicadoInstitucional |
| `comedor_id` | Comedor/espacio (PWA) |
| `colaborador_id` | Colaborador PWA |
| `nomina_id` | Miembro Nomina PWA |
| `mensaje_id` | Mensaje PWA |
| `actividad_pwa_id` | Actividad PWA |
| `renaper_consulta_id` | Consulta RENAPER (historial interno) |

### IDs de entidades VAT

| Variable | Entidad |
|----------|---------|
| `provincia_id` | Provincia |
| `municipio_id` | Municipio |
| `plan_id` | PlanCurricular |
| `curso_id` | Curso |
| `comision_curso_id` | ComisionCurso |
| `sector_id` | Sector |
| `subsector_id` | Subsector |
| `titulo_id` | TituloReferencia |
| `modalidad_id` | Modalidad |
| `programa_id` | Programa |
| `ciudadano_id` | Ciudadano |
| `voucher_id` | Voucher |
| `documento` | DNI ciudadano (VAT Web) |
| `cuil` | CUIL ciudadano (VAT Web) |

### GESTIONAR (AppSheet)

| Variable | Descripción |
|----------|-------------|
| `gestionarApiKey` | `applicationAccessKey` (secret) |
| `gestionarComedorAction` | URL tabla `Comedores` |
| `gestionarRelevamientoAction` | URL tabla `RelevamientoComedores` |
| `gestionarDiasPrestacionAction` | URL tabla `DiasPrestacion` |
| `gestionarPrimerSeguimientoAction` | URL tabla `Seguimientos1erVisita` |

### RENAPER (API Externa)

| Variable | Descripción |
|----------|-------------|
| `renaperBaseUrl` | URL base API RENAPER |
| `renaperUsername` | Usuario login |
| `renaperPassword` | Contraseña login (secret) |
| `renaperAuthToken` | Bearer token (se guarda automáticamente via test script) |

---

## Variables de entorno Django relevantes

| Variable Django | Descripción |
|----------------|-------------|
| `GESTIONAR_API_KEY` | Clave de autenticación AppSheet (= `gestionarApiKey`) |
| `GESTIONAR_API_COMEDORES` | URL acción tabla Comedores |
| `GESTIONAR_API_CREAR_PRIMER_SEGUIMIENTO` | URL acción tabla Seguimientos1erVisita |
| `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO` | URL acción tabla Seguimientos1erVisita (mismo endpoint) |
| `RENAPER_API_URL` | URL base API RENAPER (= `renaperBaseUrl`) |
| `RENAPER_API_USERNAME` | Usuario RENAPER |
| `RENAPER_API_PASSWORD` | Contraseña RENAPER |
| `TICKETERA_ENABLED` | Si es `False`, todos los endpoints `/api/ticketera/` devuelven 503 |
| `ENABLE_API_DOCS` | Si es `True`, habilita `/api/schema/`, `/api/docs/`, `/api/redoc/` |
