FROM nvidia/cuda:11.4.3-base-ubuntu20.04

# Instala las dependencias para compilar Python
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
    liblzma-dev

# Descarga y compila Python 3.8.10 (o la versión que desees)
RUN wget https://www.python.org/ftp/python/{{PYTHON_VERSION}}/Python-{{PYTHON_VERSION}}.tgz && \
    tar xzf Python-{{PYTHON_VERSION}}.tgz && \
    cd Python-{{PYTHON_VERSION}} && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall

# Crea un alias para python3.8
RUN ln -s /usr/local/bin/python3.8 /usr/bin/python3 && \
    ln -s /usr/local/bin/pip3.8 /usr/bin/pip

# Instala las dependencias de tu aplicación
RUN pip install --no-cache-dir {{REQUIREMENTS}}

# Limpia los archivos de instalación
RUN rm -rf /Python-{{PYTHON_VERSION}}*

# Configura el alias para que el comando 'python' apunte a 'python3'
RUN ln -s /usr/bin/python3 /usr/bin/python
