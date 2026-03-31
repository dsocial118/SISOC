# Configuración del Sistema de Vouchers - VAT

## Descripción General

El sistema de vouchers permite asignar créditos de formación a ciudadanos para que se inscriban en ofertas formativas. Cada voucher tiene:

- **Cantidad inicial**: Créditos asignados
- **Cantidad usada**: Créditos consumidos
- **Cantidad disponible**: Créditos pendientes de usar
- **Fecha de vencimiento**: Límite de validez
- **Estado**: activo, vencido, agotado, cancelado

## Configuración en Django Settings

### Variables de Configuración

```python
# settings.py

VOUCHER_CONFIG = {
    "ENABLED": True,                          # Activar/desactivar sistema
    "RECARGA_AUTOMATICA": True,               # Habilitar recargas automáticas
    "DIA_RECARGA": 1,                         # Día del mes para recarga (1-31)
    "CANTIDAD_RECARGA": 50,                   # Créditos a recargar por voucher
    "PROGRAMA_DEFECTO": "Programa VAT",       # Programa por defecto para nuevos vouchers
    "DIAS_ANTES_VENCIMIENTO_NOTIFICACION": 7, # Días para notificar antes de vencer
}
```

### Configuración Recomendada por Entorno

**Producción:**
```python
VOUCHER_CONFIG = {
    "ENABLED": True,
    "RECARGA_AUTOMATICA": True,
    "DIA_RECARGA": 1,
    "CANTIDAD_RECARGA": 50,
    "PROGRAMA_DEFECTO": "Programa VAT",
    "DIAS_ANTES_VENCIMIENTO_NOTIFICACION": 7,
}
```

**Desarrollo/Testing:**
```python
VOUCHER_CONFIG = {
    "ENABLED": True,
    "RECARGA_AUTOMATICA": False,  # Desactivar para tests
    "DIA_RECARGA": 1,
    "CANTIDAD_RECARGA": 10,        # Cantidad menor para testing
    "PROGRAMA_DEFECTO": "Test Program",
    "DIAS_ANTES_VENCIMIENTO_NOTIFICACION": 1,
}
```

## Configuración de Cron

### Requisitos

- Servidor Linux/Unix con acceso a `crontab`
- Usuario con permisos para ejecutar comandos Django
- Entorno virtual activado (si aplica)

### Configurar Recarga Automática Mensual

Editar el crontab:
```bash
crontab -e
```

Agregar línea para ejecutar el 1° de cada mes a medianoche:
```cron
# Recarga automática de vouchers - 1° de mes a las 00:00
0 0 1 * * cd /ruta/a/backoffice && python manage.py recargar_vouchers --execute >> /var/log/voucher_reload.log 2>&1
```

Ejemplo completo con entorno virtual:
```cron
0 0 1 * * cd /home/sisoc/backoffice && /home/sisoc/venv/bin/python manage.py recargar_vouchers --execute >> /var/log/voucher_reload.log 2>&1
```

### Configuración Alternativa: Recarga Semanal

```cron
# Cada lunes a las 02:00
0 2 * * 1 cd /ruta/a/backoffice && python manage.py recargar_vouchers --execute
```

### Configuración Alternativa: Recarga Diaria (Testing)

```cron
# Diariamente a las 23:00 (testing)
0 23 * * * cd /ruta/a/backoffice && python manage.py recargar_vouchers --execute
```

## Uso del Management Command

### Comando Básico

Ver qué se recargaría sin hacer cambios:
```bash
python manage.py recargar_vouchers --check
```

Ejecutar la recarga:
```bash
python manage.py recargar_vouchers --execute
```

### Opciones Avanzadas

**Recargar solo un programa:**
```bash
python manage.py recargar_vouchers --execute --programa=1
```

**Cambiar cantidad de créditos:**
```bash
python manage.py recargar_vouchers --execute --cantidad=100
```

**Modo test (sin cambios):**
```bash
python manage.py recargar_vouchers --test
```

**Verificar sin ejecutar:**
```bash
python manage.py recargar_vouchers --check --programa=2 --cantidad=30
```

### Ejemplos Prácticos

```bash
# Ver qué se recargaría para el programa 1
python manage.py recargar_vouchers --check --programa=1

# Recargar todos los vouchers con 50 créditos
python manage.py recargar_vouchers --execute

# Recargar solo vouchers del programa "Formación" (id=2) con 75 créditos
python manage.py recargar_vouchers --execute --programa=2 --cantidad=75

# Test de recarga sin hacer cambios
python manage.py recargar_vouchers --test --cantidad=30
```

## Monitoreo y Logs

### Archivo de Log

El comando genera logs en:
```
/var/log/voucher_reload.log
```

### Ver Últimos Logs

```bash
tail -50 /var/log/voucher_reload.log
```

### Monitorear en Tiempo Real

```bash
tail -f /var/log/voucher_reload.log
```

### Logs en Django Admin

Todos los eventos de voucher se registran en `VoucherLog` visible en:
```
/admin/vat/voucherlog/
```

## API REST

### Endpoints Disponibles

**Listar vouchers:**
```
GET /api/vat/vouchers/
GET /api/vat/vouchers/?ciudadano_id=1
GET /api/vat/vouchers/?estado=activo
GET /api/vat/vouchers/?programa_id=1
```

**Obtener detalle de voucher:**
```
GET /api/vat/vouchers/{id}/
```

**Obtener crédito disponible:**
```
GET /api/vat/vouchers/{id}/disponible/
```

**Obtener vouchers por ciudadano:**
```
GET /api/vat/vouchers/por_ciudadano/?ciudadano_id=1
```

### Ejemplo: Consultar Voucher

```bash
AUTH_HEADER="Authorization: Bearer <tu_api_key>"
curl -H "$AUTH_HEADER" \
  "http://localhost/api/vat/vouchers/?ciudadano_id=123"
```

Respuesta:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 42,
      "ciudadano": 123,
      "ciudadano_nombre": "Juan Pérez",
      "programa": 1,
      "programa_nombre": "Programa VAT",
      "cantidad_inicial": 50,
      "cantidad_usada": 15,
      "cantidad_disponible": 35,
      "estado": "activo",
      "fecha_asignacion": "2026-01-15",
      "fecha_vencimiento": "2026-12-31",
      "dias_para_vencimiento": 285,
      "recargas": [
        {
          "id": 1,
          "cantidad": 50,
          "motivo": "automatica",
          "fecha_recarga": "2026-01-15T00:00:00Z",
          "autorizado_por": 1,
          "autorizado_por_nombre": "Admin"
        }
      ],
      "usos": [
        {
          "id": 5,
          "inscripcion_oferta": 10,
          "cantidad_usada": 15,
          "fecha_uso": "2026-02-20T14:30:00Z"
        }
      ]
    }
  ]
}
```

## Casos de Uso

### Caso 1: Recarga Automática Mensual

**Configuración:**
- `DIA_RECARGA`: 1 (primer día del mes)
- `CANTIDAD_RECARGA`: 50 créditos
- Cron: `0 0 1 * *`

**Flujo:**
1. El 1° de mes a las 00:00, cron ejecuta `recargar_vouchers --execute`
2. Sistema busca todos los vouchers activos/agotados y vigentes
3. Suma 50 créditos a cada uno
4. Registra la recarga en `VoucherRecarga` y `VoucherLog`
5. Genera notificación (si se implementa)

### Caso 2: Recarga Manual por Programa

Un administrador necesita recargar vouchers de un programa específico:

```bash
python manage.py recargar_vouchers --execute --programa=3 --cantidad=100
```

Sistema procesará solo vouchers del programa 3 con 100 créditos cada uno.

### Caso 3: Crear Voucher Manualmente

Desde Django Admin:
1. Ir a `/admin/vat/voucher/add/`
2. Seleccionar ciudadano y programa
3. Ingresar cantidad inicial y fecha de vencimiento
4. Guardar
5. Sistema crea registro en `VoucherLog` automáticamente

### Caso 4: Usar Voucher en Inscripción

Cuando se inscribe ciudadano a una oferta:
1. Sistema valida si tiene voucher disponible
2. Descuenta créditos automáticamente
3. Registra uso en `VoucherUso`
4. Actualiza `cantidad_usada` y `cantidad_disponible`

## Troubleshooting

### El comando no encuentra vouchers

```bash
# Verificar vouchers disponibles
python manage.py recargar_vouchers --check

# Si no hay salida, revisar:
# 1. ¿Hay vouchers en la BD?
# 2. ¿Están activos o agotados?
# 3. ¿No están vencidos?
```

### Error: "No system or admin user found"

La recarga registra cambios con un usuario "sistema". Si no existe:
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.create_user('sistema', password='secure_password')
```

### Cron no se ejecuta

Verificar:
```bash
# Ver trabajos cron activos
crontab -l

# Ver log del sistema
grep CRON /var/log/syslog

# Verificar permisos
ls -la /ruta/a/backoffice/manage.py
```

### Verificar Logs

```bash
# Últimos 10 eventos de voucher en Django
django-admin shell <<< "from VAT.models import VoucherLog; \
print('\n'.join(f'{l.voucher}: {l.get_tipo_evento_display()}' \
for l in VoucherLog.objects.all()[:10]))"
```

## Mejores Prácticas

1. **Hacer backup** antes de cambios importantes en `VOUCHER_CONFIG`
2. **Testear** cambios con `--check` antes de ejecutar
3. **Monitorear logs** después de cada recarga automática
4. **Revisar vencimientos** semanalmente desde `/admin/vat/voucher/`
5. **Documentar recargas manuales** en `detalles` de `VoucherLog`
6. **Configurar alertas** si hay vouchers próximos a vencer

## Soporte

Para reportar problemas o solicitar cambios:
- Revisar `VoucherLog` en admin
- Consultar logs en `/var/log/voucher_reload.log`
- Contactar al equipo de desarrollo
