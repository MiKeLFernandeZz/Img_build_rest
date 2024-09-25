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
        "use_gpu": use_gpu
    }

    # credentials_volume_mount = k8s.V1VolumeMount(
    #     name="docker-config", mount_path="/kaniko/.docker"
    # )

    # credentials_container_volume_mounts = [
    #     k8s.V1VolumeMount(mount_path="/kaniko/.docker", name="docker-config")
    # ]

    # credentials_volume = k8s.V1Volume(name="docker-config", empty_dir=k8s.V1EmptyDirVolumeSource())

    # credentials_container = k8s.V1Container(
    #     name="create-config",
    #     image="alpine:latest",
    #     command=["sh", "-c"],
    #     args=[
    #         "mkdir -p /kaniko/.docker && "
    #         f"echo -n ${user}:${password}"
    #     ],
    #     volume_mounts=credentials_container_volume_mounts
    # )

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

    # Crear el volumen para las dependencias de git
    # dag_dependencies_volume = k8s.V1Volume(name="dag-dependencies", empty_dir=k8s.V1EmptyDirVolumeSource())


    # Definición de la tarea para construir la imagen
    # image_build_task = KubernetesPodOperator(
    #     task_id='image_build',
    #     name='image_build',
    #     namespace='airflow',
    #     image='mfernandezlabastida/kaniko:1.0',
    #     env_vars=env_vars,
    #     init_containers=[init_container],  # Añadir ambos init containers
    #     volumes=[volume],
    #     volume_mounts=[volume_mount],
    #     # cmds=["/kaniko/executor"],
    #     # arguments=[
    #     #     f"--dockerfile={path}/Dockerfile",
    #     #     f"--context={path}",
    #     #     f"--destination={endpoint}",
    #     #     f"--build-arg=PYTHON_VERSION={python_version}"
    #     # ]
    #     cmds=["sh", "-c"],
    #     arguments=[
    #         f"echo -n ${user}:${password} && "
    #         f"auth=$(echo -n \"${user}:${password}\" | base64) && "
    #         "echo '{\"auths\": {\"https://index.docker.io/v1/\": {\"auth\": \"'${auth}'\"}}}' > /kaniko/.docker/config.json && "
    #         f"/kaniko/executor --dockerfile={path}/Dockerfile --context={path} --destination={endpoint} --build-arg=PYTHON_VERSION={python_version}"
    #     ]
    # )

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

        # Configurar logging
        logging.info("Starting image build task")

        # Obtener las credenciales de las variables de entorno
        user = os.getenv('user')
        password = os.getenv('password')
        endpoint = os.getenv('endpoint')
        python_version = os.getenv('python_version')
        use_gpu = os.getenv('use_gpu')
        requirements = os.getenv('requirements')
        required_packages = ['mlflow', 'redis', 'psycopg2-binary']
        path = '/git/Img_build_rest/docker'

        # Verificar si se va a usar GPU
        logging.warning(f"Use GPU: {use_gpu}")
        if use_gpu == 'true':
            logging.warning("Using GPU")
            path = '/git/Img_build_rest/docker_gpus'

        # Verificar si las dependencias se encuentran en el requirements.txt
        requirements_list = requirements.split()
        for package in required_packages:
            if package not in requirements_list:
                requirements_list.append(package)

        requirements = ' '.join(requirements_list)

        # requirement format --> 'package1==1.0.0 package2==2.0.0'
        packages = requirements.split()

        with open(f'{path}/requirements.txt', 'w') as f:
            for package in packages:
                f.write(package + '\n')

        # Autenticación para Docker
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

        # Ejecutar Kaniko
        logging.warning("Running Kaniko executor")
        logging.warning(f"Path: {path}")
        logging.warning(f"Endpoint: {endpoint}")
        logging.warning(f"Python version: {python_version}")
        logging.warning(f"Requirements: {requirements}")

        result = subprocess.run(
            [
                "/kaniko/executor",
                f"--dockerfile={path}/Dockerfile",
                f"--context={path}",
                f"--destination={endpoint}",
                f"--build-arg=PYTHON_VERSION={python_version}"
            ],
            check=True  # Lanza una excepción si el comando devuelve un código diferente de cero
        )

        logging.warning(f"Kaniko executor finished with return code: {result.returncode}")

    image_build_task()

# Llamar al DAG
DAG_image_build_REST()
