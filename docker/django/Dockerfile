FROM python:3.9.19-bullseye

WORKDIR /sisoc

# Envs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=es_AR.UTF-8
ENV LC_ALL=es_AR.UTF-8
ENV DJANGO_DEBUG=True
ENV DJANGO_SECRET_KEY="Y8OaXQMLNTdcdH43PbS4ZAMa0AKZUp9aJJKd0ELGViNBEJ8TPfZlOwx6tI"
ENV DJANGO_ALLOWED_HOSTS="localhost 127.0.0.1 [::1]"
ENV DATABASE_HOST="mysql"
ENV DATABASE_PORT="3307"
ENV DATABASE_USER="root"
ENV DATABASE_PASSWORD="root1-password2"
ENV DATABASE_NAME="sisoc-local"

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    gcc \
    libc-dev \
    bash \
    mariadb-client \
    dos2unix \
    locales && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configure locales
RUN echo "es_AR.UTF-8 UTF-8" >> /etc/locale.gen && \
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen && \
    echo "LANG=es_AR.UTF-8" > /etc/default/locale && \
    echo "LC_ALL=es_AR.UTF-8" >> /etc/default/locale

# App dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Add and make entrypoint script executable
COPY ./docker/django/entrypoint.sh /sisoc/docker/django/entrypoint.sh
RUN chmod +x ./docker/django/entrypoint.sh && \
    dos2unix ./docker/django/entrypoint.sh

# CMD to start the application
CMD ["./docker/django/entrypoint.sh"]
