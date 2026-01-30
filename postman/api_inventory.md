# API Inventory

## Internal APIs (Own APIs)

| Endpoint | Method | Module | Source File | Auth Required |
|----------|--------|--------|-------------|---------------|
| `api/centrodefamilia/centros/` | CRUD | Centro de Familia | [centrodefamilia/api_views.py](file:///home/juanikitro/BACKOFFICE/centrodefamilia/api_views.py) | Yes (Token/API Key) |
| `api/centrodefamilia/actividades/` | CRUD | Centro de Familia | [centrodefamilia/api_views.py](file:///home/juanikitro/BACKOFFICE/centrodefamilia/api_views.py) | Yes (Token/API Key) |
| `api/centrodefamilia/categorias/` | CRUD | Centro de Familia | [centrodefamilia/api_views.py](file:///home/juanikitro/BACKOFFICE/centrodefamilia/api_views.py) | Yes (Token/API Key) |
| `api/centrodefamilia/beneficiarios/` | CRUD | Centro de Familia | [centrodefamilia/api_views.py](file:///home/juanikitro/BACKOFFICE/centrodefamilia/api_views.py) | Yes (Token/API Key) |
| `api/centrodefamilia/responsables/` | CRUD | Centro de Familia | [centrodefamilia/api_views.py](file:///home/juanikitro/BACKOFFICE/centrodefamilia/api_views.py) | Yes (Token/API Key) |
| `api/centrodefamilia/cabal-registros/` | CRUD | Centro de Familia | [centrodefamilia/api_views.py](file:///home/juanikitro/BACKOFFICE/centrodefamilia/api_views.py) | Yes (Token/API Key) |
| `api/centrodefamilia/provincias/` | Read | Ubicación | [centrodefamilia/api_views.py](file:///home/juanikitro/BACKOFFICE/centrodefamilia/api_views.py) | Yes (Token/API Key) |
| `api/relevamiento` | PATCH | Relevamientos | [relevamientos/views/api_views.py](file:///home/juanikitro/BACKOFFICE/relevamientos/views/api_views.py) | Yes (HasAPIKeyOrToken) |
| `api/schema/` | GET | OpenAPI | [config/urls.py](file:///home/juanikitro/BACKOFFICE/config/urls.py) | AllowAny |

## External APIs (Integrations)

| Service | Endpoint Description | Env Method | Source File |
|---------|----------------------|------------|-------------|
| **Gestionar** | Sync/Create Comedor | `POST` (Action: Find/Add/Update) | [comedores/management/commands/sync_comedores_gestionar.py](file:///home/juanikitro/BACKOFFICE/comedores/management/commands/sync_comedores_gestionar.py) |
| **Gestionar** | Get Territoriales | `POST` (Action: Find) | [comedores/services/territorial_service.py](file:///home/juanikitro/BACKOFFICE/comedores/services/territorial_service.py) |
| **RENAPER** | Login (Get Token) | `POST /auth/login` | [centrodefamilia/services/consulta_renaper.py](file:///home/juanikitro/BACKOFFICE/centrodefamilia/services/consulta_renaper.py) |
| **RENAPER** | Consultar Ciudadano | `GET /consultarenaper` | [centrodefamilia/services/consulta_renaper.py](file:///home/juanikitro/BACKOFFICE/centrodefamilia/services/consulta_renaper.py) |

## Environment Variables Used

- `GESTIONAR_API_CREAR_COMEDOR`: Base Endpoint for Comedores sync.
- `GESTIONAR_API_KEY`: Auth Header `applicationAccessKey`.
- `RENAPER_API_URL`: Base URL for Renaper.
- `RENAPER_API_USERNAME`: Login User.
- `RENAPER_API_PASSWORD`: Login Pass.
