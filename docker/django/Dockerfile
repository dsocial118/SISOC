FROM python:3.9.19-bullseye

WORKDIR /sisoc

# Variables de entorno generales para Python y el sistema
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
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
      locales && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configuración de locales
RUN echo "es_AR.UTF-8 UTF-8" >> /etc/locale.gen && \
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen && \
    echo "LANG=es_AR.UTF-8" > /etc/default/locale && \
    echo "LC_ALL=es_AR.UTF-8" >> /etc/default/locale

# Instalación de dependencias de la aplicación
COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && \
    pip install pymysql

# Agrega el script de entrypoint y hazlo ejecutable
COPY ./docker/django/entrypoint.py ./docker/django/entrypoint.py

# Comando de inicio de la aplicación
CMD ["python", "./docker/django/entrypoint.py"]
