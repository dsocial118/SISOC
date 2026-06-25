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

## Preprocesamiento de imagen

Antes de pasar cada imagen a Tesseract, el sistema aplica un pipeline de
limpieza con OpenCV (`ocr/services_preprocess.py`, función
`preprocess_for_ocr`) para mejorar la precisión en documentos "sucios":
sellos superpuestos, fondos grises, texto inclinado y ruido de digitalización.

El pipeline aplica, en orden:

1. Conversión a escala de grises.
2. Redimensionado si el lado mayor es menor a 1500px (~300 DPI efectivos).
3. Binarización adaptativa (`cv2.adaptiveThreshold`, método Gaussian, bloque 31, C=10).

El preprocesamiento es **best-effort**: ante cualquier error se registra el
problema y se usa la imagen original, sin interrumpir el OCR.

Se aplica tanto a imágenes (`_extract_from_image`) como a cada página de un
PDF (`_extract_from_pdf`, que además se renderiza a 300 DPI). Se puede
desactivar con el setting `OCR_PREPROCESS=False` (ver Variables de entorno)
si aparecen regresiones.

### Por qué no hay deskew ni denoise morfológico

Se evaluó el pipeline empíricamente contra un documento real (acta + estatuto
escaneado de 14 páginas, con sello y firmas) midiendo el recall de palabras
contra una transcripción de referencia:

| Configuración | Recall |
|---|---|
| Sin preprocesar (baseline) | 0.963 |
| Grises + adaptativa bloque 31 (**actual**) | **0.971** |
| + deskew (`minAreaRect`) | 0.957 (peor) |
| Pipeline inicial (adaptativa 11 + morfología + deskew) | **0.420** |

Conclusiones:

- El **deskew** con `cv2.minAreaRect` sobre la página completa es poco fiable y
  además, con la convención de ángulo de OpenCV ≥ 4.5 (rango `(0, 90]`),
  producía rotaciones de ~90° que destruían el texto. Aun corregido no mejoró
  el reconocimiento, por lo que se removió.
- La **morfología** (MORPH_CLOSE) no aportó mejora medible y se removió.
- Un **bloque adaptativo grande (31)** tolera mejor fondos grises y sellos que
  el bloque chico (11) sin fragmentar caracteres.

Los sellos **negros superpuestos** sobre el texto y la escritura manuscrita no
son recuperables con preprocesamiento de imagen; para llegar a un texto
"limpio" se requiere un paso posterior de corrección con LLM (ver Próximos
pasos).

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
| `OCR_PREPROCESS` | `True` | Activa el preprocesamiento de imagen con OpenCV antes del OCR |

## Dependencias del sistema (Docker)

Las siguientes dependencias se instalan en el Dockerfile:

```
tesseract-ocr          # Motor OCR
tesseract-ocr-spa      # Paquete de idioma español
poppler-utils          # Conversión de PDF a imágenes (pdf2image)
```

## Dependencias Python

```
pytesseract==0.3.13              # Wrapper Python para Tesseract
pdf2image==1.17.0                # Conversión PDF → imágenes para OCR
opencv-python-headless==4.10.0.84  # Preprocesamiento de imagen (sin deps de GUI)
```

## Tests

```bash
# Correr todos los tests del módulo OCR
python manage.py test ocr --verbosity=2

# Por archivo
python manage.py test ocr.tests.test_models
python manage.py test ocr.tests.test_services_ocr
python manage.py test ocr.tests.test_services_preprocess
python manage.py test ocr.tests.test_services_ocr_jobs
python manage.py test ocr.tests.test_views
```

Los tests usan mocks para aislar Tesseract, pdf2image y OpenCV (cv2), por lo que **no requieren que Tesseract esté instalado localmente**.

## Evaluación de calidad (recall)

Para medir el impacto de cambios en el preprocesado o en la configuración de
Tesseract hay un comando que procesa un archivo con el pipeline real y lo
compara contra un texto de referencia (*ground-truth*), reportando recall /
precision / F1 de palabras (ver `ocr/eval_metrics.py`):

```bash
# Recall del pipeline actual contra un ground-truth
python manage.py ocr_eval --file ruta/al/documento.pdf --ground-truth ruta/al/referencia.txt

# Baseline sin preprocesado (para comparar antes/después)
python manage.py ocr_eval --file documento.pdf --ground-truth referencia.txt --no-preprocess
```

El *recall* (proporción de palabras del ground-truth recuperadas por el OCR) es
la métrica principal: es robusta frente a orden, espaciado y puntuación. El
archivo y el ground-truth se pasan por argumento y **no se versionan** (pueden
contener datos personales).

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
5. Vista de administración para que superusuarios vean todos los lotes (no solo los propios).
