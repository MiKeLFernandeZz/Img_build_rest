

FROM python:3.9.17
# FROM registry-docker-registry.registry.svc.cluster.local:5001/python:3.9.17
# Establece el directorio de trabajo en /app
WORKDIR /app 

# Crear un archivo temporal para las dependencias
# COPY requirements.txt .

# Instala las dependencias especificadas en el archivo temporal
RUN pip install --no-cache-dir pandas==1.3.3

# ENTRYPOINT ["python", "app.py"]
