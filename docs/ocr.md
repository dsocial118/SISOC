# Módulo OCR

Extracción de texto a partir de imágenes y PDFs usando Tesseract OCR.

## Uso (pantalla)

1. Ir a **Administración del sistema → OCR** en el sidebar.
2. Seleccionar uno o varios archivos (JPG, JPEG, PNG o PDF).
3. (Opcional) En **Opciones de calidad** se pueden desactivar, por lote, el
   preprocesado de imagen, la capa de texto del PDF y la auto-orientación.
   Vienen **activadas** (mejor calidad); desactivarlas puede degradar el OCR.
   La configuración elegida queda registrada en el lote y se muestra en su
   detalle. Las opciones que degradan al activarse (tessdata_best, corrección
   ortográfica, remoción de sellos de color) no se exponen acá: se controlan por
   settings/env (ver más abajo).
4. Hacer clic en **Procesar archivos**.
5. El sistema crea un lote y redirige al detalle.
6. Actualizar la página hasta que el lote cambie a **Completado**.
7. Para cada archivo se muestra el texto extraído, con botones para copiar y descargar como `.txt`.

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

## Híbrido: capa de texto embebida del PDF

Muchos PDFs son *born-digital* (generados por software, con capa de texto
perfecta) en algunas páginas y escaneos puros en otras. Para esas páginas
digitales el OCR es innecesario y peor que leer el texto embebido. El módulo
decide **por página** entre usar el texto embebido (con `pypdf`) o el OCR.

### Heurística (conservadora, "que no se pierda nada")

Para cada página se calcula el texto embebido y el texto OCR, y se usa la capa
embebida **solo si**:

1. tiene al menos `OCR_PDF_TEXT_LAYER_MIN_WORDS` palabras (texto sustancial), y
2. la página **no** contiene un raster de tamaño-página
   (`OCR_PDF_TEXT_LAYER_IMG_MAXSIDE`), que delataría un escaneo, y
3. **no tiene menos palabras que el OCR** de esa misma página.

El punto 3 es el **guardrail anti-pérdida**: si la capa embebida es *parcial*
(p. ej. un encabezado digital sobre un cuerpo escaneado), tendrá menos palabras
que el OCR de la página completa, y entonces se usa el OCR para no perder el
cuerpo. Ante cualquier duda → OCR. Se garantiza que el texto híbrido **nunca
tiene menos palabras que el OCR-only**, y esto se loguea por documento
(`OCR PDF hibrido: ... palabras hibrido=N ocr_only=M`).

La lectura de la capa de texto es *best-effort*: si `pypdf` falla, se cae a OCR
puro sin interrumpir el procesamiento. Se controla con `OCR_PDF_TEXT_LAYER`.

### Medición sobre el documento de prueba

En el acta + estatuto escaneado de 14 páginas usado como referencia, las
páginas 14-15 son born-digital pero su capa de texto resultó ser un
**subconjunto** de lo rasterizado (sellos y códigos GEDO que el OCR también
lee): la capa tenía 18 y 39 palabras frente a 27 y 90 del OCR. Por eso el
guardrail mantiene el OCR en esas páginas y el recall global no cambia
(0.962, sin regresión). En PDFs born-digital *completos* el híbrido entrega el
texto digital perfecto. Nota: el OCR se ejecuta igual en todas las páginas para
poder comparar y aplicar el guardrail.

## Worker asincrónico

El procesamiento OCR no bloquea la request HTTP. Un worker dedicado procesa los lotes pendientes en segundo plano.

### Local (Docker Compose, dev)

El `docker-compose.yml` de desarrollo incluye un servicio `ocr_worker`
gestionado (con `restart: unless-stopped`) que arranca el worker
automáticamente y se reinicia solo si se cae:

```bash
docker compose up -d ocr_worker
docker compose logs -f ocr_worker   # ver actividad
```

Sin este servicio (o con el worker caído) los lotes quedan en **pendiente**
indefinidamente. También se puede correr el worker a mano dentro del contenedor:

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
| `OCR_PDF_TEXT_LAYER` | `True` | Usa la capa de texto embebida en páginas born-digital del PDF (con guardrail anti-pérdida) |
| `OCR_PDF_TEXT_LAYER_MIN_WORDS` | `8` | Mínimo de palabras embebidas para considerar una página born-digital |
| `OCR_PDF_TEXT_LAYER_IMG_MAXSIDE` | `1000` | Lado mayor (px) de un raster a partir del cual se asume escaneo de página |
| `OCR_TESSDATA_DIR` | `` (vacío) | Directorio de modelos Tesseract. Vacío = modelo del sistema. Apuntar a `/usr/share/tessdata-best` para usar tessdata_best |
| `OCR_SPELLCHECK` | `False` | Corrección ortográfica local del texto OCR (offline). OFF por default: degrada el recall en escaneos |
| `OCR_AUTO_ORIENT` | `True` | Corrige la orientación (90/180/270°) con el OSD de Tesseract antes del OCR (best-effort) |
| `OCR_REMOVE_COLOR_STAMPS` | `False` | Blanquea tinta de color (sellos azul/rojo) por saturación HSV antes de binarizar |
| `OCR_COLOR_SAT_THRESHOLD` | `90` | Saturación HSV (0-255) sobre la cual un píxel se considera tinta de color |
| `OCR_TESSERACT_PSM` | `-1` | Page segmentation mode de Tesseract. `-1` = default de Tesseract (psm 3) |
| `OCR_TESSERACT_OEM` | `-1` | OCR engine mode de Tesseract. `-1` = default de Tesseract |

## Modelo de Tesseract (tessdata_best)

El paquete `tesseract-ocr-spa` de Debian instala el modelo *fast* del español
(~2.3 MB). El repositorio oficial `tessdata_best` ofrece un modelo LSTM de mayor
precisión (~13.5 MB), que el Dockerfile descarga a `/usr/share/tessdata-best`.

Está **disponible pero desactivado por defecto**: el setting `OCR_TESSDATA_DIR`
viene vacío (modelo del sistema). Para activarlo, definir
`OCR_TESSDATA_DIR=/usr/share/tessdata-best`. La selección es *fallback-safe*: si
el directorio no contiene `<lang>.traineddata`, se omite la flag y Tesseract usa
el modelo del sistema (se loguea un warning).

**Por qué está OFF por defecto:** sobre el documento de prueba (escaneo sellado
binarizado) el modelo *best* **degradó** el recall frente al *fast* del sistema:

| Configuración | Recall |
|---|---|
| fast (sistema) + preprocesado (**actual**) | **0.962** |
| best + preprocesado | 0.954 |
| best sin preprocesado | 0.938 |

El modelo *best* está optimizado para imágenes limpias; sobre escaneos
binarizados con sellos rinde peor. Conviene evaluarlo por tipo de documento
antes de activarlo en producción.

## Parámetros de Tesseract (PSM / OEM)

El `--psm` (page segmentation mode) y el `--oem` (OCR engine mode) de Tesseract
son configurables vía `OCR_TESSERACT_PSM` / `OCR_TESSERACT_OEM`. Un valor `-1`
(default) **omite la flag** y deja que Tesseract use su default (psm 3, motor
LSTM), preservando el comportamiento actual.

**Default elegido por evidencia.** Medición de recall sobre el documento de
prueba (acta + estatuto, mixto: texto, tablas y formularios):

| Configuración | Recall |
|---|---|
| psm 3 / default (**actual**) | **0.962** |
| psm 6 (bloque uniforme) | 0.960 |
| psm 4 (columna) | 0.960 |
| oem 1 (LSTM) / oem 3 (default) | 0.962 (sin diferencia) |

En este documento mixto el psm 3 (segmentación automática) supera levemente al
psm 6, y el oem no mueve la aguja (el sistema ya usa LSTM). Por eso el default
se deja en los valores de Tesseract. El `--psm 6` puede convenir en documentos
de **texto denso uniforme** (una sola columna sin tablas).

Opcionalmente Tesseract admite `--user-words` / `--user-patterns` con
vocabulario legal y patrones (DNI, N° de expediente). No se implementó porque la
ganancia sobre este corpus fue nula y agrega gestión de archivos; queda como
afinamiento futuro si aparece un caso que lo justifique.

## Remoción de sellos de color (OCR_REMOVE_COLOR_STAMPS)

Como paso opcional del preprocesado (antes de pasar a grises), se puede eliminar
la tinta de color de los sellos: se convierte la imagen a HSV y los píxeles con
saturación mayor a `OCR_COLOR_SAT_THRESHOLD` (azules, rojos) se llevan a blanco.
El texto negro tiene baja saturación, por lo que se preserva.

**Limitación conocida:** los sellos **negros** superpuestos tienen baja
saturación igual que el texto, así que este método **no puede separarlos** (ver
también la sección de preprocesamiento).

Está **OFF por defecto** (`OCR_REMOVE_COLOR_STAMPS=False`). En el documento de
prueba los sellos son oscuros (baja saturación), por lo que activarlo **no
cambia el recall** (0.962, sin regresión). Es útil para documentos con sellos de
color saturado superpuestos al texto.

## Auto-corrección de orientación (OCR_AUTO_ORIENT)

Antes del OCR de cada imagen o página de PDF, se usa el OSD (*Orientation and
Script Detection*) de Tesseract (`pytesseract.image_to_osd`) para detectar si la
página está rotada 90/180/270° y, de ser así, rotarla para dejarla derecha. Se
aplica sobre la imagen original (no binarizada), donde el OSD es más fiable.

Es **best-effort**: si el OSD falla (poco texto, sin confianza, error), se
continúa sin rotar. Activado por defecto (`OCR_AUTO_ORIENT=True`); sobre el
documento de prueba (ya derecho) no cambia el recall (0.962, sin regresión) y
aporta robustez ante escaneos rotados.

## Corrección ortográfica (OCR_SPELLCHECK)

`ocr/services_postprocess.py::correct_text` aplica una corrección ortográfica
**local y offline** (con `pyspellchecker`, diccionario español embebido) al
texto extraído, al final de `extract_text_from_file`. Es muy conservadora:

- solo toca palabras enteramente en minúscula (preserva nombres propios,
  siglas y encabezados en mayúscula),
- solo corrige tokens **fuera de diccionario**, a **un edit de distancia**,
- no toca números ni puntuación,
- no degrada plurales válidos ausentes del diccionario (`documentos`),
- protege un vocabulario de dominio (artículo, comisión directiva, personería,
  estatuto, asamblea, etc.),
- conserva el texto crudo en `raw_text` cuando corrige.

Es **best-effort**: ante cualquier error devuelve el texto sin tocar.

**Por qué está OFF por defecto:** el recall sobre el documento de prueba bajó de
**0.962 a 0.861** con la corrección activa. El diccionario de frecuencias
español es incompleto y "corrige" muchas palabras válidas del texto legal. Su
beneficio real (restaurar acentos) además **no se refleja en el recall**, que
normaliza acentos. Conviene activarlo solo con un diccionario de dominio más
completo y validación por tipo de documento.

## Dependencias del sistema (Docker)

Las siguientes dependencias se instalan en el Dockerfile:

```
tesseract-ocr          # Motor OCR
tesseract-ocr-spa      # Paquete de idioma español (modelo fast)
poppler-utils          # Conversión de PDF a imágenes (pdf2image)
wget, ca-certificates   # Descarga del modelo tessdata_best
```

Además, el Dockerfile descarga `spa.traineddata` de `tessdata_best` en
`/usr/share/tessdata-best` (ver sección anterior; desactivado por defecto).

## Dependencias Python

```
pytesseract==0.3.13              # Wrapper Python para Tesseract
pdf2image==1.17.0                # Conversión PDF → imágenes para OCR
opencv-python-headless==4.10.0.84  # Preprocesamiento de imagen (sin deps de GUI)
pypdf==6.8.0                     # Capa de texto embebida del PDF (híbrido)
pyspellchecker==0.8.1            # Corrección ortográfica offline (opcional, OFF)
```

(`pypdf` ya estaba en requirements para otros usos; el híbrido lo reutiliza.)

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
# Mejoras de precisión:
python manage.py test ocr.tests.test_pdf_text_layer       # híbrido capa de texto
python manage.py test ocr.tests.test_tesseract_config     # tessdata_best / psm / oem
python manage.py test ocr.tests.test_services_postprocess  # corrección ortográfica
python manage.py test ocr.tests.test_auto_orient          # OSD / orientación
python manage.py test ocr.tests.test_color_stamps         # remoción de sellos de color
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

## Resumen de mejoras de precisión y recall

Seis mejoras gratuitas y locales (sin LLM), cada una con su setting y medidas
una por una sobre el documento de prueba (acta + estatuto escaneado de 15
páginas; ground-truth reconstruido de texto impreso verificado + capa digital).
Baseline del pipeline actual: **recall 0.962**.

| # | Mejora | Setting | Default | Recall | Decisión |
|---|--------|---------|---------|--------|----------|
| 1 | Híbrido capa de texto del PDF | `OCR_PDF_TEXT_LAYER` | `True` | 0.962 | ON; guardrail evita perder contenido. En este doc la capa digital era parcial → se mantiene OCR |
| 2 | Modelo tessdata_best | `OCR_TESSDATA_DIR` | OFF | 0.954 | OFF: degrada en escaneos binarizados; disponible para activar |
| 3 | Corrección ortográfica | `OCR_SPELLCHECK` | `False` | 0.861 | OFF: degrada; diccionario es incompleto |
| 4 | Auto-orientación (OSD) | `OCR_AUTO_ORIENT` | `True` | 0.962 | ON: sin regresión, robustez ante rotaciones |
| 5 | Remoción sellos de color | `OCR_REMOVE_COLOR_STAMPS` | `False` | 0.962 | OFF: sin sellos de color en el doc; sin regresión |
| 6 | Tuning PSM/OEM | `OCR_TESSERACT_PSM`/`OEM` | `-1` (default) | 0.962 | Default psm 3 es el mejor (psm 6/4 = 0.960) |

Conclusión: el recall global se mantiene en **0.962** (sin regresión respecto del
baseline) con los defaults elegidos. Las mejoras que degradaban quedaron OFF con
evidencia; las neutras/robustas (1, 4) quedaron ON. El valor de varias mejoras
(capa digital perfecta, acentos, sellos de color, rotación) aplica a otros tipos
de documento y/o no se refleja en la métrica de recall (que normaliza acentos).

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
