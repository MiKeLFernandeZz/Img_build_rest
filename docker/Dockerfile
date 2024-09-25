ARG PYTHON_VERSION="3.9.17"

FROM python:${PYTHON_VERSION}
# FROM registry-docker-registry.registry.svc.cluster.local:5001/python:3.9.17
# Establece el directorio de trabajo en /app
WORKDIR /app 

# Crear un archivo temporal para las dependencias
# COPY requirements.txt .
COPY ./requirements.txt /app/requirements.txt

# Instala las dependencias especificadas en el archivo temporal
RUN pip install --no-cache-dir -r requirements.txt
# ENTRYPOINT ["python", "app.py"]