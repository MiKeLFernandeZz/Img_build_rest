ARG PYTHON_VERSION="3.9.17"
ARG REQUIREMENTS="numpy"

FROM python:${PYTHON_VERSION}

# Establece el directorio de trabajo en /app
WORKDIR /app 

# Crear un archivo temporal para las dependencias
# RUN echo "${REQUIREMENTS}" > requirements.txt

# Instala las dependencias especificadas en el archivo temporal
RUN pip install --no-cache-dir -r requirements.txt
