# Guía de Despliegue - Optimización de Imágenes WebP

## 📋 Resumen

Esta guía documenta el proceso seguro para desplegar la optimización de imágenes WebP en producción, minimizando riesgos y permitiendo rollback en caso de problemas.

---

## 🎯 ¿Qué hace esta feature?

1. **Conversión automática a WebP**: Convierte JPG, PNG, BMP, TIFF a formato WebP (25-35% más liviano)
2. **Lazy loading nativo**: Las imágenes cargan solo cuando son visibles (mejor performance)
3. **Fallback automático**: Si algo falla, usa la imagen original
4. **Sin cambios en DB**: No modifica las imágenes originales, solo crea versiones .webp adicionales

---

## ✅ Pre-requisitos en Producción

### 1. Dependencias Python
Agregar a `requirements.txt`:
```txt
Pillow>=10.0.0
tqdm>=4.66.0
```

### 2. Verificar permisos de escritura
El contenedor Docker debe poder **escribir** en el directorio de media:
```bash
# Dentro del contenedor
docker exec -it <container_name> bash
touch /app/media/test_write.txt
rm /app/media/test_write.txt
```

Si falla, ajustar permisos del volumen:
```bash
# En el host
sudo chown -R 1000:1000 /path/to/media/volume
sudo chmod -R 775 /path/to/media/volume
```

### 3. Espacio en disco
Verificar espacio disponible (las imágenes WebP ocupan ~70% del original):
```bash
df -h /path/to/media
```

**Ejemplo**: Si tienes 10GB de imágenes, necesitas ~7GB adicionales (temporalmente serán ~17GB total).

---

## 🚀 Proceso de Despliegue (PASO A PASO)

### Fase 1: Despliegue del Código (Horario normal)

#### 1.1. Actualizar código en servidor
```bash
git pull origin main
```

#### 1.2. Reconstruir contenedor con nuevas dependencias
```bash
docker-compose build web
docker-compose up -d
```

#### 1.3. Verificar logs
```bash
docker-compose logs -f web
```

Buscar errores relacionados con Pillow o imports.

#### 1.4. Cargar template tags
En cualquier template que uses imágenes, agregar al inicio:
```django
{% load image_tags %}
```

Y reemplazar:
```django
<!-- Antes -->
<img src="{{ ciudadano.foto.url }}" alt="Foto">

<!-- Después -->
{% optimized_image ciudadano.foto "Foto del ciudadano" css_class="img-fluid" %}
```

**IMPORTANTE**: Los templates con el código viejo seguirán funcionando igual. Puedes migrar de a poco.

---

### Fase 2: Conversión Masiva de Imágenes (FUERA DE HORARIO)

#### 2.1. Modo DRY-RUN (Simulación sin cambios reales)
**Ejecutar PRIMERO esto para ver qué haría sin modificar nada:**

```bash
docker exec -it <container_name> python manage.py generate_webp_images --dry-run --stats
```

Esto mostrará:
- Cuántas imágenes encontró
- Cuánto espacio se ahorraría
- **NO genera ningún archivo**

**Ejemplo de output esperado:**
```
🔍 Modo DRY RUN - No se generarán archivos

📸 ImageFields encontrados: 5
  - ciudadanos.Ciudadano.foto
  - ciudadanos.Ciudadano.foto_dni
  - comedores.Comedor.imagen
  - operadores.Operador.avatar
  - noticias.Noticia.imagen_portada

======================================================================
Procesando: ciudadanos.Ciudadano.foto
======================================================================
Imágenes a procesar: 15234
...
```

#### 2.2. Prueba limitada (10 imágenes)
**Probar con pocas imágenes primero:**

```bash
docker exec -it <container_name> python manage.py generate_webp_images --limit 10 --stats
```

Verificar que:
- ✅ Se crean archivos .webp en media
- ✅ Los archivos tienen tamaño correcto (no están vacíos)
- ✅ La app sigue funcionando
- ✅ Las imágenes se ven correctamente en el navegador

#### 2.3. Conversión por modelo (Recomendado)
**Procesar un modelo específico a la vez:**

```bash
# Solo fotos de ciudadanos
docker exec -it <container_name> python manage.py generate_webp_images --app ciudadanos --model Ciudadano --stats

# Solo imágenes de comedores
docker exec -it <container_name> python manage.py generate_webp_images --app comedores --stats
```

**Ventajas:**
- Puedes detener entre modelos si hay problemas
- Monitoreas espacio en disco por etapas
- Si falla un modelo, no afecta a los demás

#### 2.4. Conversión completa (Todo de una vez)
**Solo después de probar lo anterior:**

```bash
docker exec -it <container_name> python manage.py generate_webp_images --stats --quality 85
```

**NOTA**: Este comando puede tomar horas si hay muchas imágenes. Ejecutar con `nohup` o `screen`:

```bash
docker exec -it <container_name> bash
nohup python manage.py generate_webp_images --stats --quality 85 > /tmp/webp_conversion.log 2>&1 &
exit

# Ver progreso
docker exec -it <container_name> tail -f /tmp/webp_conversion.log
```

---

## 📊 Monitoreo Durante la Conversión

### Ver progreso en tiempo real
```bash
docker exec -it <container_name> tail -f /tmp/webp_conversion.log
```

### Verificar espacio en disco
```bash
docker exec -it <container_name> df -h /app/media

# En el host
watch -n 5 "df -h | grep media"
```

### Contar archivos WebP generados
```bash
docker exec -it <container_name> find /app/media -name "*.webp" | wc -l
```

### Ver CPU/Memoria del contenedor
```bash
docker stats <container_name>
```

---

## 🛡️ Mitigación de Riesgos

### Riesgo 1: Permisos de escritura
**Síntoma**: Error "Permission denied" al crear archivos

**Solución**:
```bash
# En el host
sudo chown -R 1000:1000 /path/to/media
sudo chmod -R 775 /path/to/media

# Reiniciar contenedor
docker-compose restart web
```

### Riesgo 2: Sin espacio en disco
**Síntoma**: Error "No space left on device"

**Solución**:
```bash
# Detener conversión (Ctrl+C o buscar proceso)
docker exec -it <container_name> ps aux | grep generate_webp
docker exec -it <container_name> kill <PID>

# Limpiar archivos WebP generados
docker exec -it <container_name> find /app/media -name "*.webp" -delete

# Liberar espacio y reintentar por partes
```

### Riesgo 3: Imágenes corruptas
**Síntoma**: Algunos WebP no se crean o están vacíos

**Qué pasa**: El servicio tiene fallback automático, usa la imagen original

**Logs para debug**:
```bash
docker-compose logs web | grep "Error convirtiendo"
```

### Riesgo 4: Conversión tarda demasiado
**Síntoma**: El comando lleva más de X horas

**Solución**: Procesar por lotes
```bash
# Procesar 100 imágenes a la vez
docker exec -it <container_name> python manage.py generate_webp_images --limit 100
# Ejecutar múltiples veces o por modelo
```

---

## 🔄 Plan de Rollback

### Si algo sale mal DESPUÉS del despliegue:

#### Opción 1: Rollback completo (volver a versión anterior)
```bash
git checkout <commit_anterior>
docker-compose build web
docker-compose up -d
```

#### Opción 2: Deshabilitar WebP temporalmente (sin rollback de código)
En `settings.py`:
```python
# Agregar esta línea para deshabilitar WebP
WEBP_ENABLED = False
```

En `image_service.py`, al inicio de `get_or_create_webp`:
```python
def get_or_create_webp(image_path: str, quality: int = WEBP_QUALITY) -> str:
    if not getattr(settings, 'WEBP_ENABLED', True):
        return image_path  # Retornar imagen original

    # ... resto del código
```

#### Opción 3: Eliminar archivos WebP (mantener código)
```bash
# Eliminar todos los archivos .webp
docker exec -it <container_name> find /app/media -name "*.webp" -delete

# Limpiar caché
docker exec -it <container_name> python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()
```

**Las imágenes originales NUNCA se tocan**, así que siempre puedes volver atrás sin pérdida de datos.

---

## 🧪 Testing en Producción (Post-despliegue)

### Test 1: Verificar que se sirven WebP
```bash
# En el navegador (Chrome DevTools > Network)
# Buscar imágenes y verificar:
# - Type: webp
# - Size: menor que antes
```

### Test 2: Verificar fallback en navegadores viejos
```bash
# En Safari antiguo o IE11
# Debe mostrar imágenes originales (JPG/PNG)
```

### Test 3: Verificar lazy loading
```bash
# En Chrome DevTools > Network
# Hacer scroll lento
# Las imágenes deben cargar solo al aparecer en pantalla
```

---

## 📈 Métricas de Éxito

Después de 1 semana en producción, verificar:

1. **Ahorro de ancho de banda**:
   ```bash
   # Comparar tráfico de media del mes anterior
   # Esperado: Reducción del 25-35%
   ```

2. **Tiempo de carga de páginas**:
   ```bash
   # Usar Google PageSpeed Insights
   # Antes vs Después
   ```

3. **Logs de errores**:
   ```bash
   docker-compose logs web | grep -i "error.*webp" | wc -l
   # Debe ser 0 o muy bajo
   ```

---

## 🔧 Configuración de docker-compose.yml

Asegurarse de que el volumen de media esté correctamente montado:

```yaml
services:
  web:
    build: .
    volumes:
      - ./media:/app/media  # Debe tener permisos de escritura
      - ./static:/app/static
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
```

---

## 💡 Recomendaciones Finales

### Para la conversión masiva:
1. ✅ Ejecutar fuera de horario (2-6 AM)
2. ✅ Hacer backup del volumen de media antes
3. ✅ Empezar con `--dry-run` siempre
4. ✅ Probar con `--limit 10` antes de todo
5. ✅ Procesar por modelo si son muchas imágenes
6. ✅ Monitorear espacio en disco durante el proceso
7. ✅ Usar `nohup` o `screen` para procesos largos

### Para el día a día:
- Las nuevas imágenes se convierten **automáticamente** on-demand
- No hace falta volver a correr el comando
- El caché mantiene todo rápido

---

## 🆘 Comandos de Emergencia

```bash
# Detener conversión en proceso
docker exec -it <container_name> pkill -f generate_webp_images

# Eliminar todos los WebP
docker exec -it <container_name> find /app/media -name "*.webp" -delete

# Limpiar caché completa
docker exec -it <container_name> python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Ver logs en tiempo real
docker-compose logs -f --tail=100 web

# Reiniciar contenedor
docker-compose restart web

# Ver uso de recursos
docker stats <container_name>
```