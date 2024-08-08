FROM python:3.9.19-bullseye

WORKDIR /sisoc

# Envs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=True
ENV DJANGO_SECRET_KEY="Y8OaXQMLNTdcdH43PbS4ZAMa0AKZUp9aJJKd0ELGViNBEJ8TPfZlOwx6tI"
ENV DJANGO_ALLOWED_HOSTS="localhost 127.0.0.1 [::1]"
ENV DATABASE_HOST="mysql"
ENV DATABASE_USER="root"
ENV DATABASE_PASSWORD="root1-password2"
ENV DATABASE_NAME="sisoc-local"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    gcc \
    libc-dev \
    bash \
    mariadb-client \
    dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# App dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Add and make entrypoint script executable
COPY ./docker/django/entrypoint.sh /sisoc/entrypoint.sh

# Convert entrypoint script to Unix format (useful for Windows compatibility)
RUN dos2unix /sisoc/entrypoint.sh

# Make sure it has execution permissions
RUN chmod +x /sisoc/entrypoint.sh

CMD sh /sisoc/docker/django/entrypoint.sh
