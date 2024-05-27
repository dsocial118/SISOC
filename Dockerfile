# Usa la imagen base oficial de Python 3.9
FROM python:3.9-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Instala dependencias del sistema necesarias para mysqlclient y locales
RUN apt-get update && \
    apt-get install -y --fix-missing gcc libmariadb-dev-compat libmariadb-dev locales && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Genera y configura locales
RUN sed -i '/es_AR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

# Copia el archivo de requerimientos
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install -r requirements.txt

# Copia el resto del código de la aplicación al directorio de trabajo
COPY . .

# Expone el puerto en el que la aplicación correrá
EXPOSE 8080

# Ejecuta los comandos necesarios para preparar la aplicación
RUN python manage.py makemigrations Usuarios Configuraciones Legajos && \
    python manage.py makemigrations && \
    python manage.py migrate && \
    python manage.py collectstatic --noinput

# Define el comando por defecto para ejecutar la aplicación
CMD ["python", "manage.py", "runserver", "localhost:8080"]
