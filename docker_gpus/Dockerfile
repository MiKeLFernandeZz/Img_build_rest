# Usa la imagen base de CUDA
FROM nvidia/cuda:11.4.3-base-ubuntu20.04

# Argumento para la versión de Python, se puede pasar en el build
ARG PYTHON_VERSION=3.8

# Establece variables de entorno para evitar preguntas durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependencias y agrega el repositorio de deadsnakes para Python
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-dev python${PYTHON_VERSION}-distutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Establece Python como predeterminado
RUN update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1

# Verifica la versión de Python instalada
RUN python --version && python3 --version

# Establece el directorio de trabajo
WORKDIR /app

# Puedes agregar más pasos según tu necesidad (como copiar archivos, instalar pip, etc.)
# Ejemplo: Copiar los archivos de la app
# COPY . /app

# Ejemplo: Instalar pip y las dependencias
RUN apt-get update && \
    apt-get install -y curl && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py && \
    rm get-pip.py

# Comando por defecto
CMD ["python"]
