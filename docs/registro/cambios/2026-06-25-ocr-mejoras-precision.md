# 2026-06-25 - OCR: seis mejoras de precisión, locales y configurables

## Contexto

El módulo OCR (`ocr/`) ya tenía preprocesado con OpenCV (recall de palabras
0.962 sobre un acta + estatuto escaneado de referencia). Se pidió subir la
precisión con mejoras **gratuitas y locales** (sin LLM pago), cada una detrás de
un setting con default conservador, midiendo recall antes/después y sin degradar
el baseline.

## Qué se agregó

Cada feature con su setting en `config/settings.py` (patrón `_safe_*_env`), tests
y documentación en `docs/ocr.md`:

1. **Híbrido capa de texto del PDF** (`OCR_PDF_TEXT_LAYER=True`): por página, usa
   el texto embebido (pypdf) en páginas born-digital y OCR en escaneos. Guardrail
   anti-pérdida: nunca usa la capa si tendría menos palabras que el OCR (capa
   parcial) ni si hay un raster de tamaño-página. Se loguea por documento.
2. **Modelo tessdata_best** (`OCR_TESSDATA_DIR=""`, OFF): el Dockerfile descarga
   `spa.traineddata` de tessdata_best a `/usr/share/tessdata-best`; selección
   fallback-safe vía `--tessdata-dir`. OFF porque degradó el recall en escaneos.
3. **Corrección ortográfica offline** (`OCR_SPELLCHECK=False`, OFF):
   `ocr/services_postprocess.py::correct_text` con pyspellchecker, conservadora
   (solo tokens fuera de diccionario, distancia 1, preserva nombres propios,
   plurales, números y vocabulario de dominio). OFF porque degradó el recall.
4. **Auto-orientación OSD** (`OCR_AUTO_ORIENT=True`): rota 90/180/270° según el
   OSD de Tesseract antes del OCR; best-effort. Sin regresión.
5. **Remoción de sellos de color HSV** (`OCR_REMOVE_COLOR_STAMPS=False`, OFF):
   blanquea tinta de color por saturación; no separa sellos negros. Sin regresión.
6. **Tuning PSM/OEM** (`OCR_TESSERACT_PSM/OEM=-1`): configurables; el default de
   Tesseract (psm 3) resultó el mejor por evidencia.

## Recall medido (documento de referencia, baseline 0.962)

| Mejora | Default | Recall |
|--------|---------|--------|
| Híbrido capa de texto | ON | 0.962 (sin regresión) |
| tessdata_best | OFF | 0.954 (degrada) |
| Spellcheck | OFF | 0.861 (degrada) |
| Auto-orientación | ON | 0.962 |
| Sellos de color | OFF | 0.962 |
| PSM/OEM (psm 3 default) | default | 0.962 (psm 6/4 = 0.960) |

El recall global se mantiene en **0.962** con los defaults elegidos. Las mejoras
que degradaban quedaron OFF con evidencia; las robustas/neutras quedaron ON. El
valor de varias mejoras aplica a otros tipos de documento o no se refleja en el
recall (que normaliza acentos).

## Impacto y notas

- Firma pública de `extract_text_from_file` intacta; tests previos del flujo de
  extracción y preprocesado siguen verdes.
- Dependencia nueva: `pyspellchecker==0.8.1` (opcional, runtime). `pypdf` ya
  estaba en requirements y se reutiliza.
- Metodología: ground-truth reconstruido (texto impreso verificado + capa
  digital de páginas born-digital), medido con `manage.py ocr_eval`.
- Fuera de alcance: 19 tests preexistentes de `ocr` ya rotos (14 por
  debug-toolbar activo en tests, 5 por desajuste test↔`_process_document` en el
  worker de jobs). No se tocaron; quedan para una tarea aparte.
