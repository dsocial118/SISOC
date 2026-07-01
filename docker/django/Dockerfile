FROM python:3.11.15-slim-bookworm

WORKDIR /sisoc

# Variables de entorno generales para Python y el sistema
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV LANG=es_AR.UTF-8
ENV LC_ALL=es_AR.UTF-8

# Instalación de dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      default-libmysqlclient-dev \
      gcc \
      libc-dev \
      bash \
      mariadb-client \
      locales \
      libpango-1.0-0 \
      libharfbuzz0b \
      libpangoft2-1.0-0 \
      libfontconfig1 \
      libcairo2 \
      tesseract-ocr \
      tesseract-ocr-spa \
      poppler-utils \
      wget \
      ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Modelo Tesseract de máxima precisión (tessdata_best, español). Queda
# disponible pero NO activo: el OCR usa el modelo del sistema por defecto. Para
# activarlo, definir OCR_TESSDATA_DIR=/usr/share/tessdata-best (ver docs/ocr.md;
# en pruebas sobre escaneos sellados el modelo best degradó el recall).
RUN mkdir -p /usr/share/tessdata-best && \
    wget -q -O /usr/share/tessdata-best/spa.traineddata \
      https://github.com/tesseract-ocr/tessdata_best/raw/main/spa.traineddata

# Configuración de locales
RUN echo "es_AR.UTF-8 UTF-8" >> /etc/locale.gen && \
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen && \
    echo "LANG=es_AR.UTF-8" > /etc/default/locale && \
    echo "LC_ALL=es_AR.UTF-8" >> /etc/default/locale

# Instalación de dependencias de la aplicación
COPY ./requirements.txt .
COPY ./requirements ./requirements
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install --no-cache-dir --retries 5 --timeout 60 -r requirements.txt

# Agrega el script de entrypoint y hazlo ejecutable
COPY ./docker/django/entrypoint.py ./docker/django/entrypoint.py

# Comando de inicio de la aplicación
CMD ["python", "./docker/django/entrypoint.py"]
