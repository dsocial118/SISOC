# Integración PAS y Prestación Alimentar desde DW

## Estado de la Integración

✅ **Completada** - Conexión al DW y visualización de datos en tabs

## Cambios Realizados

### 1. Corrección de Nombres de Columnas
**Archivo:** `ciudadanos/services/pas_service.py`

- Corregido nombre de columna en `vw_PA_ciudadanos_resumen`
- Cambio: `ciudadano_titular_key` → `idSisocRelacionTitular`
- Aplicado en ambas queries (obtener_datos_pas y obtener_historial_pas)

### 2. Validación de Índices
**Archivo:** `ciudadanos/views.py` - método `get_pas_context`

- Agregada validación de longitud antes de acceder a índices
- Validación: `if resumen and len(resumen) >= 7:`
- Validación en list comprehension: `p[0] if len(p) > 0 else None`
- Mejora de manejo de excepciones: específicas (ConnectionError, ValueError) + genérica

### 3. Actualización de Templates
**Archivo:** `ciudadanos/templates/ciudadanos/ciudadano_detail.html`

#### Tab PAS
- Muestra datos de `vw_pas_ciudadanos_resumen`:
  - Estado
  - Monto
  - Fecha Inicio
  - Fecha Baja
  - Última Liquidación
  - Aviso Liquidación

#### Tab Prestación Alimentar
- Muestra tabla con datos de `vw_PA_ciudadanos_resumen`:
  - Rol (ciudadano_programa_rol_desc)
  - Monto
  - Período (periodo_mes)
  - Titular (idSisocRelacionTitular)

## Vistas del DW Utilizadas

### vw_pas_ciudadanos_resumen
```sql
SELECT 
  ciudadano_id_sisoc,
  UltimoEstadoPas,
  FechaInicioPas,
  FechaBajaPas,
  FechaUltimaLiquidacion,
  monto,
  AvisoLiquidacion
FROM DW_sisoc.vw_pas_ciudadanos_resumen
WHERE ciudadano_id_sisoc = ?
```

### vw_PA_ciudadanos_resumen
```sql
SELECT 
  ciudadano_id_sisoc,
  ciudadano_programa_rol_desc,
  monto,
  periodo_mes,
  idSisocRelacionTitular
FROM DW_sisoc.vw_PA_ciudadanos_resumen
WHERE ciudadano_id_sisoc = ?
ORDER BY periodo_mes DESC
```

## Configuración Requerida

En `.env`:
```
DW_DATABASE_HOST=mysql
DW_DATABASE_PORT=3306
DW_DATABASE_USER=root
DW_DATABASE_PASSWORD=root1-password2
DW_DATABASE_NAME=DW_sisoc
```

En `config/settings.py`:
```python
DATABASES = {
    ...
    "dw_sisoc": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DW_DATABASE_NAME", "DW_sisoc"),
        "USER": os.environ.get("DW_DATABASE_USER"),
        "PASSWORD": os.environ.get("DW_DATABASE_PASSWORD"),
        "HOST": os.environ.get("DW_DATABASE_HOST"),
        "PORT": os.environ.get("DW_DATABASE_PORT", "3306"),
        ...
    }
}
```

## Manejo de Errores

- Conexión fallida: Retorna `{"error": str(e), "resumen": None, "programas": []}`
- Datos incompletos: Valida longitud antes de acceder
- Excepciones específicas: ConnectionError, ValueError
- Excepciones genéricas: Logged pero no expuestas al usuario

## Testing

Para verificar la integración:

1. Acceder a `/ciudadanos/<id>/` 
2. Navegar a tab "PAS"
3. Verificar que se muestren datos de `vw_pas_ciudadanos_resumen`
4. Navegar a tab "Prestación Alimentar"
5. Verificar que se muestre tabla con datos de `vw_PA_ciudadanos_resumen`

## Próximos Pasos

- [ ] Agregar filtros por período en Prestación Alimentar
- [ ] Implementar gráficos de evolución de montos
- [ ] Agregar exportación a PDF
- [ ] Implementar caché para queries frecuentes
