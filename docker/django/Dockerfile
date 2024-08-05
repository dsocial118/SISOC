FROM python:3.9.19-alpine

WORKDIR /sisoc

# Envs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_DEBUG=True
ENV DJANGO_SECRET_KEY="Y8OaXQMLNTdcdH43PbS4ZAMa0AKZUp9aJJKd0ELGViNBEJ8TPfZlOwx6tI"
ENV DJANGO_ALLOWED_HOSTS="localhost 127.0.0.1 [::1]"
ENV DATABASE_HOST="mysql"
ENV DATABASE_USER="root"
ENV DATABASE_PASSWORD="root1-password2"
ENV DATABASE_NAME="sisoc-local"

# System dependencies
RUN apk update && apk add --no-cache mariadb-connector-c-dev gcc musl-dev bash mariadb-client

# App dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Add and make entrypoint script executable
COPY ./docker/django/entrypoint.sh /sisoc/entrypoint.sh
RUN chmod +x /sisoc/entrypoint.sh

CMD ["/sisoc/docker/django/entrypoint.sh"]