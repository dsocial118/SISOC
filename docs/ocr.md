# Módulo OCR

Extracción de texto a partir de imágenes y PDFs usando Tesseract OCR.

## Uso (pantalla)

1. Ir a **Administración del sistema → OCR** en el sidebar.
2. Seleccionar uno o varios archivos (JPG, JPEG, PNG o PDF).
3. Hacer clic en **Procesar archivos**.
4. El sistema crea un lote y redirige al detalle.
5. Actualizar la página hasta que el lote cambie a **Completado**.
6. Para cada archivo se muestra el texto extraído, con botones para copiar y descargar como `.txt`.

## Formatos soportados

| Formato | Notas |
|---------|-------|
| JPG / JPEG | Imágenes de cualquier origen |
| PNG | Imágenes de cualquier origen |
| PDF | Texto nativo y escaneos; soporta multipágina |

## Permisos

El permiso requerido es `ocr.use_ocr`. Los superusuarios tienen acceso sin necesidad del permiso.

Para dar acceso a un grupo:
1. Ir a **Admin → Auth → Grupos**.
2. Seleccionar el grupo.
3. Agregar el permiso **ocr | Lote OCR | Puede usar el módulo OCR**.

## Worker asincrónico

El procesamiento OCR no bloquea la request HTTP. Un worker dedicado procesa los lotes pendientes en segundo plano.

### Local

```bash
python manage.py process_ocr_jobs
# Con --once para procesar un ciclo y salir (útil en tests):
python manage.py process_ocr_jobs --once
```

### Docker (producción)

El servicio `ocr_worker` en `docker-compose.produccion.yml` arranca el worker automáticamente:

```bash
docker compose -f docker-compose.produccion.yml up ocr_worker
```

La variable de entorno que lo activa es:

```
DJANGO_SERVICE_ROLE=ocr_worker
```

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `OCR_JOB_POLL_SECONDS` | `2` | Segundos entre ciclos de polling del worker |
| `OCR_JOB_STALE_SECONDS` | `600` | Segundos sin actividad para marcar un job como fallido |
| `OCR_MAX_FILE_SIZE_MB` | `20` | Tamaño máximo por archivo en MB |
| `OCR_LANGUAGE` | `spa` | Código de idioma Tesseract (spa = español) |

## Dependencias del sistema (Docker)

Las siguientes dependencias se instalan en el Dockerfile:

```
tesseract-ocr          # Motor OCR
tesseract-ocr-spa      # Paquete de idioma español
poppler-utils          # Conversión de PDF a imágenes (pdf2image)
```

## Dependencias Python

```
pytesseract==0.3.13    # Wrapper Python para Tesseract
pdf2image==1.17.0      # Conversión PDF → imágenes para OCR
```

## Tests

```bash
# Correr todos los tests del módulo OCR
python manage.py test ocr --verbosity=2

# Por archivo
python manage.py test ocr.tests.test_models
python manage.py test ocr.tests.test_services_ocr
python manage.py test ocr.tests.test_services_ocr_jobs
python manage.py test ocr.tests.test_views
```

Los tests usan mocks para aislar Tesseract y pdf2image, por lo que **no requieren que Tesseract esté instalado localmente**.

## Limitaciones del MVP

- Idioma OCR fijo en español (configurable por env var, no por usuario).
- No hay extracción estructurada de campos.
- No hay validación documental ni clasificación.
- No hay integración con otras entidades del sistema.
- No hay parseo con LLM.
- Los archivos se eliminan del servidor una vez procesados (no hay descarga posterior del original).
- No hay reintentos automáticos por documento fallido.

## Próximos pasos sugeridos

1. Extracción estructurada de campos (nombre, DNI, fecha, etc.) usando regex o LLM sobre el texto extraído.
2. Clasificación automática de tipo de documento.
3. Integración con flujos de admisiones, ciudadanos u otras entidades.
4. Soporte multi-idioma seleccionable por el usuario.
5. Pre-procesamiento de imagen (rotación, contraste) para mejorar calidad de OCR.
6. Vista de administración para que superusuarios vean todos los lotes (no solo los propios).
