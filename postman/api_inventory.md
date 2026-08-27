# API Inventory — SISOC

Todas las APIs (internas y externas) están documentadas en la colección única:
**`SISOC APIs.postman_collection.json`** · 244 requests · 11 carpetas · entorno: `Local.postman_environment.json`

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
| VAT | 148 | Cobertura completa del router público VAT; ver detalle abajo |
| Integraciones Externas | 12 | GESTIONAR (AppSheet) + RENAPER API externa |
| Docs | 2 | OpenAPI schema SISOC + VAT (`/api/schema/`) |

---

## VAT (148 requests)

| Subcarpeta | Requests | Endpoints principales |
|-----------|----------|----------------------|
| 0 - Guía de uso y autenticación | 0 | configuración, autenticación, encadenamiento de IDs y advertencias para escrituras |
| 1 - API operativa - Geografía | 6 | provincias, municipios y localidades; list y retrieve |
| 2 - API operativa - Centros e institución | 26 | centros, búsqueda por CUE vigente/histórico, acción `activos`, contactos, identificadores y ubicaciones institucionales; CRUD completo |
| 3 - API operativa - Catálogos y planes | 36 | modalidades institucionales/de cursada, sectores, subsectores, títulos y planes curriculares; CRUD completo |
| 4 - API operativa - Cursos y comisiones | 14 | cursos, `buscar`, `prioritarios` y comisiones de curso; CRUD completo |
| 5 - API operativa - Oferta institucional | 18 | ofertas institucionales, comisiones legacy y horarios; CRUD completo |
| 6 - API operativa - Inscripciones y vouchers | 26 | inscripciones de oferta, vouchers, acciones `disponible`/`por_ciudadano`, inscripciones generales y de curso; CRUD completo |
| 7 - API operativa - Evaluaciones | 12 | evaluaciones y resultados; CRUD completo |
| 8 - API web | 10 | centros, títulos y cursos (list/retrieve), `voucher-estado`, listado/alta/prevalidación de inscripciones |

La cobertura corresponde a los métodos de negocio registrados en
`VAT/api_urls.py`: GET, POST, PUT, PATCH y DELETE según cada ViewSet, más sus
acciones custom. No se duplican HEAD/OPTIONS generados automáticamente por DRF y
no se incluyen vistas HTML ni AJAX internas de `VAT/urls.py`.

La consulta `GET /api/vat/centros/?cue=<CUE>` mantiene la paginación habitual y
devuelve la ficha institucional/formativa ampliada del Centro. Busca CUE vigente,
histórico o código legacy, y excluye alumnos, inscripciones, evaluaciones,
vouchers individuales y documentos de contactos.

---

## Integraciones Externas (12 requests)

| Servicio | Acción | Método | Tabla / Endpoint |
|----------|--------|--------|-----------------|
| GESTIONAR (AppSheet) | Find/Crear/Borrar Comedor | POST | `Comedores` |
| GESTIONAR (AppSheet) | Crear/Eliminar Relevamiento | POST | `RelevamientoComedores` |
| GESTIONAR (AppSheet) | Crear DiasPrestacion | POST | `DiasPrestacion` |
| GESTIONAR (AppSheet) | Crear/Eliminar PrimerSeguimiento | POST | `Seguimientos1erVisita` |
| GESTIONAR (AppSheet) | Crear Referente | POST | `Referentes` |
| GESTIONAR (AppSheet) | Crear Observación | POST | `Observaciones` |
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
| `allowVatMutations` | Guard del ambiente activo; `false` omite POST/PUT/PATCH/DELETE VAT |
| `cue` | CUE para buscar un Centro VAT, vigente o histórico |

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
| `localidad_id` | Localidad |
| `plan_id` | PlanCurricular |
| `curso_id` | Curso |
| `comision_curso_id` | ComisionCurso |
| `sector_id` | Sector |
| `subsector_id` | Subsector |
| `titulo_id` | TituloReferencia |
| `modalidad_id` | Modalidad (variable legacy) |
| `modalidad_institucional_id` | ModalidadInstitucional |
| `modalidad_cursada_id` | ModalidadCursada |
| `programa_id` | Programa |
| `ciudadano_id` | Ciudadano |
| `voucher_id` | Voucher |
| `institucion_contacto_id` | InstitucionContacto |
| `institucion_identificador_id` | InstitucionIdentificadorHist |
| `institucion_ubicacion_id` | InstitucionUbicacion |
| `oferta_institucional_id` | OfertaInstitucional |
| `comision_id` | Comisión de oferta institucional |
| `comision_horario_id` | ComisionHorario |
| `inscripcion_oferta_id` | InscripcionOferta |
| `inscripcion_id` | Inscripcion general |
| `inscripcion_curso_id` | Inscripción expuesta por `/inscripciones-curso/` |
| `solicitud_inscripcion_id` | SolicitudInscripcionPublica devuelta por el alta web |
| `evaluacion_id` | Evaluacion |
| `resultado_evaluacion_id` | ResultadoEvaluacion |
| `usuario_id` | Usuario que registra un resultado |
| `dia_semana_id` | Día usado en un horario de comisión |
| `documento` | DNI ciudadano (VAT Web) |
| `cuil` | CUIL ciudadano (VAT Web) |

### GESTIONAR (AppSheet)

| Variable | Descripción |
|----------|-------------|
| `gestionarApiKey` | `applicationAccessKey` (secret) |
| `gestionarComedorAction` | URL tabla `Comedores` (alta y find) |
| `gestionarBorrarComedorAction` | URL tabla `Comedores` (baja) |
| `gestionarRelevamientoAction` | URL tabla `RelevamientoComedores` |
| `gestionarDiasPrestacionAction` | URL tabla `DiasPrestacion` |
| `gestionarPrimerSeguimientoAction` | URL tabla `Seguimientos1erVisita` |
| `gestionarReferenteAction` | URL tabla `Referentes` |
| `gestionarObservacionAction` | URL tabla `Observaciones` |

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
| `GESTIONAR_API_COMEDORES` | URL acción tabla Comedores (alta) |
| `GESTIONAR_API_BORRAR_COMEDOR` | URL acción tabla Comedores (baja) |
| `GESTIONAR_API_CREAR_REFERENTE` | URL acción tabla Referentes |
| `GESTIONAR_API_CREAR_OBSERVACION` | URL acción tabla Observaciones |
| `GESTIONAR_API_CREAR_PRIMER_SEGUIMIENTO` | URL acción tabla Seguimientos1erVisita |
| `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO` | URL acción tabla Seguimientos1erVisita (mismo endpoint) |
| `RENAPER_API_URL` | URL base API RENAPER (= `renaperBaseUrl`) |
| `RENAPER_API_USERNAME` | Usuario RENAPER |
| `RENAPER_API_PASSWORD` | Contraseña RENAPER |
| `TICKETERA_ENABLED` | Si es `False`, todos los endpoints `/api/ticketera/` devuelven 503 |
| `ENABLE_API_DOCS` | Si es `True`, habilita `/api/schema/`, `/api/docs/`, `/api/redoc/` |
