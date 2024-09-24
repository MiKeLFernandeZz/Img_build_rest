from datetime import datetime
from airflow.decorators import dag
from kubernetes.client import models as k8s
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.models import Variable
import base64

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
    
    # Codificación base64 de las credenciales
    encoded_auth = "{{ (dag_run.conf.get('user') + ':' + dag_run.conf.get('password')).encode('utf-8') | b64encode }}"
    
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
        "pass": password,
        "endpoint": endpoint,
        "python_version": python_version,
        "use_gpu": use_gpu
    }

    # Define el volumen para compartir entre initContainer y el container principal
    volume = k8s.V1Volume(name="docker-config", empty_dir=k8s.V1EmptyDirVolumeSource())

    # Init container para crear el archivo config.json con las credenciales en base64
    init_container = k8s.V1Container(
        name="create-config",
        image="alpine:latest",
        command=["sh", "-c"],
        args=[f'echo \'{{"auths": {{"https://index.docker.io/v1/": {{"auth": "{encoded_auth}"}}}}}}\' > /config/config.json'],
        volume_mounts=[k8s.V1VolumeMount(mount_path="/config", name="docker-config")]
    )

    # Contenedor para clonar el repositorio
    git_clone_container = k8s.V1Container(
        name="git-clone",
        image="alpine/git:latest",
        command=["sh", "-c", "mkdir -p /git && cd /git && git clone -b main --single-branch https://github.com/MiKeLFernandeZz/Img_build_rest.git"],
        volume_mounts=[k8s.V1VolumeMount(mount_path="/git", name="dag-dependencies")]
    )

    # Montaje del volumen en el pod de Kaniko
    volume_mount = k8s.V1VolumeMount(
        name="docker-config",
        mount_path="/kaniko/.docker/"
    )

    # Crear el volumen para las dependencias de git
    dag_dependencies_volume = k8s.V1Volume(name="dag-dependencies", empty_dir=k8s.V1EmptyDirVolumeSource())

    path = '/git/Img_build_rest/docker'

    # Definición de la tarea para construir la imagen
    image_build_task = KubernetesPodOperator(
        task_id='image_build',
        name='image_build',
        namespace='airflow',
        image='gcr.io/kaniko-project/executor:latest',
        env_vars=env_vars,
        init_containers=[init_container, git_clone_container],  # Añadir ambos init containers
        volumes=[volume, dag_dependencies_volume],
        volume_mounts=[volume_mount, k8s.V1VolumeMount(mount_path="/git", name="dag-dependencies")],
        cmds=["/kaniko/executor"],
        arguments=[
            f"--dockerfile={path}/Dockerfile",
            f"--context={path}",
            f"--destination={endpoint}",
            f"--build-arg=PYTHON_VERSION={python_version}"
        ]
    )

# Llamar al DAG
DAG_image_build_REST()
