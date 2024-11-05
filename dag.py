from datetime import datetime
from airflow.decorators import dag
from kubernetes.client import models as k8s
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.decorators import dag, task
from airflow.models import Variable

@dag(
    description='Generate Docker image',
    schedule_interval=None, 
    start_date=datetime(2024, 6, 25),
    catchup=False,
    tags=['core', 'img_build'],
)
def DAG_image_build_REST():

    # Variables con las credenciales y configuración desde dag_run.conf
    user = "{{ dag_run.conf.get('user') }}"
    password = "{{ dag_run.conf.get('password') }}"
    endpoint = "{{ dag_run.conf.get('endpoint') }}"
    requirements = "{{ dag_run.conf.get('requirements') }}"
    python_version = "{{ dag_run.conf.get('python_version') }}"
    use_gpu = "{{ dag_run.conf.get('use_gpu') }}"
    packages = "{{ dag_run.conf.get('packages') }}"
    cuda_version = "{{ dag_run.conf.get('cuda_version') }}"
    server_py = "{{ dag_run.conf.get('server_py') }}"
    model_uri = "{{ dag_run.conf.get('model_uri') }}"

    # Variables de entorno desde Airflow Variables y otras
    env_vars = {
        "POSTGRES_USERNAME": Variable.get("POSTGRES_USERNAME"),
        "POSTGRES_PASSWORD": Variable.get("POSTGRES_PASSWORD"),
        "POSTGRES_DATABASE": Variable.get("POSTGRES_DATABASE"),
        "POSTGRES_HOST": Variable.get("POSTGRES_HOST"),
        "POSTGRES_PORT": Variable.get("POSTGRES_PORT"),
        "TRUE_CONNECTOR_EDGE_IP": Variable.get("CONNECTOR_EDGE_IP"),
        "TRUE_CONNECTOR_EDGE_PORT": Variable.get("IDS_EXTERNAL_ECC_IDS_PORT"),
        "TRUE_CONNECTOR_CLOUD_IP": Variable.get("CONNECTOR_CLOUD_IP"),
        "TRUE_CONNECTOR_CLOUD_PORT": Variable.get("IDS_PROXY_PORT"),
        "MLFLOW_ENDPOINT": Variable.get("MLFLOW_ENDPOINT"),
        "MLFLOW_TRACKING_URI": Variable.get("MLFLOW_ENDPOINT"),
        "MLFLOW_TRACKING_USERNAME": Variable.get("MLFLOW_TRACKING_USERNAME"),
        "MLFLOW_TRACKING_PASSWORD": Variable.get("MLFLOW_TRACKING_PASSWORD"),
        "container": "docker",
        "requirements": requirements,
        "user": user,
        "password": password,
        "endpoint": endpoint,
        "python_version": python_version,
        "use_gpu": use_gpu,
        "cuda_version": cuda_version,
        "packages": packages,
        "server_py": server_py,
        "model_uri": model_uri
    }

    volume_mount = k8s.V1VolumeMount(
        name="dag-dependencies", mount_path="/git"
    )

    # Contenedor para clonar el repositorio
    init_container_volume_mounts = [
        k8s.V1VolumeMount(mount_path="/git", name="dag-dependencies")
    ]

    volume = k8s.V1Volume(name="dag-dependencies", empty_dir=k8s.V1EmptyDirVolumeSource())

    init_container = k8s.V1Container(
        name="git-clone",
        image="alpine/git:latest",
        command=["sh", "-c", "mkdir -p /git && cd /git && git clone -b main --single-branch https://github.com/MiKeLFernandeZz/Img_build_rest.git"],
        volume_mounts=init_container_volume_mounts
    )

    @task.kubernetes(
        image='mfernandezlabastida/kaniko:1.0',
        name='image_build',
        task_id='image_build',
        namespace='airflow',
        init_containers=[init_container],
        volumes=[volume],
        volume_mounts=[volume_mount],
        env_vars=env_vars
    )
    def image_build_task():
        import logging
        import os
        import base64
        import json
        import subprocess
        import mlflow
        import mlflow.pyfunc

        # Configurar logging
        logging.info("Starting image build task")

        # Obtener las credenciales de las variables de entorno
        user = os.getenv('user')
        password = os.getenv('password')
        endpoint = os.getenv('endpoint')
        python_version = os.getenv('python_version')
        use_gpu = os.getenv('use_gpu')
        requirements = os.getenv('requirements')
        apt_packages = os.getenv('packages')
        cuda_version = os.getenv('cuda_version')
        required_packages = ['mlflow', 'redis', 'psycopg2-binary']
        path = '/git/Img_build_rest/docker'

        server_py = os.getenv('server_py')
        model_uri = os.getenv('model_uri')

        def write_requirements_file(requirements, required_packages, server_py):
            # Verificar si las dependencias se encuentran en el requirements.txt
            requirements_list = requirements.split()
            for package in required_packages:
                if package not in requirements_list:
                    requirements_list.append(package)

            requirements = ' '.join(requirements_list)

            if server_py:
                requirements += ' fastapi uvicorn pydantic pandas'

            # requirement format --> 'package1==1.0.0 package2==2.0.0' 
            packages = requirements.split()

            with open(f'{path}/requirements.txt', 'w') as f:
                for package in packages:
                    f.write(package + '\n')

        def modify_dependencies(path, apt_packages, use_gpu):
            try:
                apt_install_prefix = "RUN apt-get update && apt-get install -y --no-install-recommends"
                default_apt_packages = "build-essential"
                if use_gpu == 'true':
                    default_apt_packages = "build-essential git curl wget zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libffi-dev libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev liblzma-dev"

                with open(f'{path}/Dockerfile', 'r') as f:
                    dockerfile_lines = f.readlines()

                updated_lines = []
                for line in dockerfile_lines:
                    if line.strip().startswith(apt_install_prefix):
                        # Reemplazar la línea con los nuevos paquetes
                        updated_line = f"{apt_install_prefix} {default_apt_packages} {apt_packages} \\\n" \
                                    "    && apt-get clean \\\n" \
                                    "    && rm -rf /var/lib/apt/lists/*\n"
                        updated_lines.append(updated_line)
                    else:
                        updated_lines.append(line)

                # Escribir el nuevo contenido en el Dockerfile
                with open(f'{path}/Dockerfile', 'w') as file:
                    file.writelines(updated_lines)
            except Exception as e:
                logging.error(f"Error while updating apt packages: {e}")

        def create_credentials_file(user, password):
            logging.warning(f"Authenticating user {user}")
            auth = f"{user}:{password}".encode('utf-8')
            auth_encoded = base64.b64encode(auth).decode('utf-8')

            # Crear configuración de Docker
            docker_config = {
                "auths": {
                    "https://index.docker.io/v1/": {
                        "auth": auth_encoded
                    }
                }
            }
            config_path = '/kaniko/.docker/config.json'

            # Guardar la configuración en el archivo
            with open(config_path, 'w') as config_file:
                json.dump(docker_config, config_file)

        def download_artifacts(model_uri, path):
            mlflow.set_tracking_uri("http://mlflow-tracking.mlflow.svc.cluster.local:5000")

            local_path = mlflow.artifacts.download_artifacts(model_uri, dst_path=path)

            # Buscar el archivo model.pkl y moverlo a la carpeta local_path en caso de que se encuentre en una subcarpeta
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    if file.startswith("model"):
                        logging.info(f"Encontrado archivo model.pkl en: {root}")
                        os.rename(os.path.join(root, file), os.path.join(local_path + '/model', file))

        def remove_entrypoint():
            try:
                with open(f'{path}/Dockerfile', 'r') as f:
                    dockerfile_lines = f.readlines()

                updated_lines = []

                for line in dockerfile_lines:
                    if not (line.strip().startswith("ENTRYPOINT") or line.strip().startswith("COPY ./app.py")):
                        updated_lines.append(line)

                with open(f'{path}/Dockerfile', 'w') as file:
                    file.writelines(updated_lines)
            except Exception as e:
                logging.error(f"Error while removing entrypoint: {e}")

        def create_app_file(server_py):
            with open(f'{path}/app.py', 'w') as f:
                f.write(server_py)


        # Verificar si se va a usar GPU
        logging.warning(f"Use GPU: {use_gpu}")
        if use_gpu == 'true':
            logging.warning("Using GPU")
            path = '/git/Img_build_rest/docker_gpus'

        # Escribir el archivo requirements.txt
        write_requirements_file(requirements, required_packages, server_py)

        # Modificar las dependencias de apt
        modify_dependencies(path, apt_packages, use_gpu)

        # Autenticación para Docker
        create_credentials_file(user, password)

        # Descargar los artefactos del modelo
        if model_uri:
            download_artifacts(model_uri, path)
        else:
            # crear carpeta artifacts
            os.makedirs(f'{path}/artifacts/model', exist_ok=True)

        # Remover el entrypoint si no se va a usar FastAPI
        if not server_py:
            remove_entrypoint()
        else:
            create_app_file(server_py)

        # Ejecutar Kaniko
        logging.warning("Running Kaniko executor")
        logging.warning(f"Path: {path}")
        logging.warning(f"Endpoint: {endpoint}")
        logging.warning(f"Python version: {python_version}")
        logging.warning(f"Requirements: {requirements}")

        args = [
            "/kaniko/executor",
            f"--dockerfile={path}/Dockerfile",
            f"--context={path}",
            f"--destination={endpoint}",
        ]

        if python_version and python_version != "None":
            args.append(f"--build-arg=PYTHON_VERSION={python_version}")

        if apt_packages and apt_packages != "None":
            args.append(f"--build-arg=APT_PACKAGES={apt_packages}")

        if cuda_version and cuda_version != "None":
            args.append(f"--build-arg=CUDA_VERSION={cuda_version}")

        logging.warning(f"Args: {args}")

        result = subprocess.run(
            args,
            check=True  # Lanza una excepción si el comando devuelve un código diferente de cero
        )

        logging.warning(f"Kaniko executor finished with return code: {result.returncode}")

    image_build_task()

# Llamar al DAG
DAG_image_build_REST()
