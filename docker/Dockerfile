FROM python:3.9.18

# Establece el directorio de trabajo en /app
WORKDIR /app 

# Copia el archivo requirements.txt al directorio de trabajo
COPY requirements.txt .

# COPY model.pkl .
# COPY server.py .
# RUN pip install --upgrade pip


# # Instala dependencias del sistema
# RUN apt-get update && apt-get install -y cmake

# Instala las dependencias especificadas en el archivo requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Especifica el comando por defecto a ejecutar cuando se inicie el contenedor
# CMD ["python", "tu_script.py"]