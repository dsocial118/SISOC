# API de Token - Autenticación

## 📋 Resumen

Endpoint para obtener token de autenticación usando credenciales de usuario.

**URL:** `POST /api/token/`

**Autenticación:** No requerida (endpoint público)

---

## 🔐 Obtener Token

### Request

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123"
  }'
```

### Response (200 OK)

```json
{
  "token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com"
}
```

### Response (401 Unauthorized)

```json
{
  "error": "Credenciales inválidas"
}
```

### Response (400 Bad Request)

```json
{
  "error": "username y password son requeridos"
}
```

---

## 💡 Ejemplos

### Con cURL

```bash
# Obtener token
TOKEN_RESPONSE=$(curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123"
  }')

# Extraer token
TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

# Usar token en solicitud
curl -X GET http://localhost:8000/api/centrodefamilia/centros/ \
  -H "Authorization: Token $TOKEN"
```

### Con Python

```python
import requests
import json

# Obtener token
response = requests.post(
    "http://localhost:8000/api/token/",
    json={
        "username": "admin",
        "password": "password123"
    }
)

if response.status_code == 200:
    data = response.json()
    token = data["token"]
    print(f"Token: {token}")
    
    # Usar token en solicitud
    headers = {"Authorization": f"Token {token}"}
    centros = requests.get(
        "http://localhost:8000/api/centrodefamilia/centros/",
        headers=headers
    )
    print(centros.json())
else:
    print(f"Error: {response.json()}")
```

### Con JavaScript/Fetch

```javascript
// Obtener token
const response = await fetch("http://localhost:8000/api/token/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    username: "admin",
    password: "password123"
  })
});

if (response.ok) {
  const data = await response.json();
  const token = data.token;
  console.log(`Token: ${token}`);
  
  // Usar token en solicitud
  const centros = await fetch(
    "http://localhost:8000/api/centrodefamilia/centros/",
    {
      headers: {
        "Authorization": `Token ${token}`
      }
    }
  );
  console.log(await centros.json());
} else {
  console.error("Error:", await response.json());
}
```

### Con Postman

**1. Crear solicitud POST**
- URL: `http://localhost:8000/api/token/`
- Method: POST
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "username": "admin",
  "password": "password123"
}
```

**2. Click "Send"**

**3. Copiar token de la respuesta**

**4. Guardar en variable de environment**
- Click en "Tests"
- Agregar script:
```javascript
var jsonData = pm.response.json();
pm.environment.set("token", jsonData.token);
```

**5. Usar en otras solicitudes**
- Header: `Authorization: Token {{token}}`

---

## 🔄 Flujo Completo

```
1. POST /api/token/
   ├─ username: "admin"
   └─ password: "password123"
   
2. Respuesta:
   ├─ token: "abc123..."
   ├─ user_id: 1
   ├─ username: "admin"
   └─ email: "admin@example.com"

3. Usar token en solicitudes:
   GET /api/centrodefamilia/centros/
   Header: Authorization: Token abc123...
   
4. Respuesta:
   {
     "count": 10,
     "results": [...]
   }
```

---

## ⚙️ Configuración en Docker

### Crear usuario (si no existe)

```bash
docker-compose exec django python manage.py createsuperuser
```

Responder preguntas:
```
Username: admin
Email: admin@example.com
Password: password123
Password (again): password123
```

### Obtener token en Docker

```bash
# Opción 1: Desde shell
docker-compose exec django python manage.py shell
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
user = User.objects.get(username='admin')
token, created = Token.objects.get_or_create(user=user)
print(f"Token: {token.key}")

# Opción 2: Desde API
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123"
  }'
```

---

## 🔒 Seguridad

### Notas Importantes

1. **No compartir tokens** - El token es como una contraseña
2. **HTTPS en producción** - Siempre usar HTTPS
3. **Expiración** - Los tokens no expiran por defecto
4. **Regenerar** - Regenerar token si se compromete

### Regenerar Token

```bash
python manage.py shell
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

user = User.objects.get(username='admin')
token = Token.objects.get(user=user)
token.delete()

# Crear nuevo token
new_token = Token.objects.create(user=user)
print(f"Nuevo token: {new_token.key}")
```

---

## 📊 Códigos de Estado

| Código | Significado |
|--------|-------------|
| 200 | OK - Token obtenido |
| 400 | Bad Request - Datos faltantes |
| 401 | Unauthorized - Credenciales inválidas |
| 500 | Server Error - Error interno |

---

## ❓ Troubleshooting

### Error: "username y password son requeridos"

**Causa:** Falta alguno de los campos

**Solución:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

### Error: "Credenciales inválidas"

**Causa:** Usuario o contraseña incorrectos

**Solución:**
1. Verificar username
2. Verificar password
3. Crear usuario si no existe

### Error: 404 Not Found

**Causa:** Endpoint no existe

**Solución:**
- Verificar URL: `http://localhost:8000/api/token/`
- Verificar que el servidor esté corriendo

---

## 🔗 Endpoints Relacionados

- `GET /api/docs/` - Documentación Swagger
- `GET /api/redoc/` - Documentación ReDoc
- `GET /api/schema/` - Schema OpenAPI

---

## 📝 Resumen

| Aspecto | Valor |
|--------|-------|
| URL | `/api/token/` |
| Método | POST |
| Autenticación | No requerida |
| Body | `{"username": "...", "password": "..."}` |
| Respuesta | `{"token": "...", "user_id": ..., ...}` |
| Códigos | 200, 400, 401 |

---

**¡Listo para usar!** 🚀
