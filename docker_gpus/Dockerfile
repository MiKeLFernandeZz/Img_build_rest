# Usa build args para especificar las versiones de CUDA, Python y los paquetes de APT a instalar
ARG CUDA_VERSION=12.6.1
ARG PYTHON_VERSION=3.11.9
ARG APT_PACKAGES="build-essential libssl-dev"

FROM nvidia/cuda:${CUDA_VERSION}-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Usar build arg para instalar paquetes adicionales de APT
ARG APT_PACKAGES
RUN apt-get update && apt-get install -y --no-install-recommends ${APT_PACKAGES} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio HOME y trabajar allí
ENV HOME="/root"
WORKDIR ${HOME}

# Instalar pyenv para gestionar versiones de Python
RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"

# Usar el build arg para establecer la versión de Python
ARG PYTHON_VERSION
RUN pyenv install ${PYTHON_VERSION} && \
    pyenv global ${PYTHON_VERSION}

# Verificar la instalación de Python
RUN python --version

# Establecer el directorio de trabajo para la aplicación
WORKDIR /app

# Copiar el archivo de dependencias
COPY requirements.txt .

# Actualizar pip e instalar dependencias desde el archivo requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
