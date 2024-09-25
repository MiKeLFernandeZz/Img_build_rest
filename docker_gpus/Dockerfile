# Especifica la versión de Python como build-arg
ARG PYTHON_VERSION="3.8.10"

FROM nvidia/cuda:11.4.3-base-ubuntu20.04

# Establece el directorio de trabajo en /app
WORKDIR /app

# Asegúrate de que el argumento se mantenga disponible en el build
ARG PYTHON_VERSION

# Instala las dependencias necesarias para compilar Python
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libncurses5-dev \
    libsqlite3-dev \
    libreadline-dev \
    libffi-dev \
    libbz2-dev \
    liblzma-dev \
    curl  # Añadimos curl para descargar pip

# Descarga, compila e instala la versión de Python especificada
RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar xzf Python-${PYTHON_VERSION}.tgz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall

# Instala pip
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python${PYTHON_VERSION%%.*} get-pip.py && \
    rm get-pip.py

# Crea un alias para el binario de Python y pip, utilizando la versión especificada
RUN ln -s /usr/local/bin/python${PYTHON_VERSION%%.*} /usr/bin/python3 && \
    ln -s /usr/local/bin/pip${PYTHON_VERSION%%.*} /usr/bin/pip

# Copia el archivo de dependencias al contenedor
COPY requirements.txt /app/requirements.txt

# Instala las dependencias de la aplicación
RUN pip install --no-cache-dir -r requirements.txt

# Limpia los archivos de instalación
RUN rm -rf /Python-${PYTHON_VERSION}*

# Configura un alias para que el comando 'python' apunte a 'python3'
RUN ln -s /usr/bin/python3 /usr/bin/python
