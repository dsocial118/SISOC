FROM python:3.9.19-alpine

WORKDIR /usr/src/app

# Envs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG=True
ENV DJANGO_SECRET_KEY="Y8OaXQMLNTdcdH43PbS4ZAMa0AKZUp9aJJKd0ELGViNBEJ8TPfZlOwx6tI"
ENV DJANGO_ALLOWED_HOSTS="localhost 127.0.0.1 [::1]"
ENV SQL_HOST="mysql"
ENV SQL_USER="root"
ENV SQL_PASSWORD="root1-password2"
ENV SQL_NAME="sisoc-local"

# System dependencies
RUN apk update && apk add --no-cache mariadb-connector-c-dev gcc musl-dev bash mariadb-client

# App dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Add and make entrypoint script executable
COPY ./docker/django/entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# Copy the project files to the container
COPY . .

CMD ["/usr/src/app/entrypoint.sh"]