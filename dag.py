from datetime import datetime
from airflow.decorators import dag, task
from kubernetes.client import models as k8s
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.models import Variable

@dag(
    description='Generate Docker image',
    schedule_interval=None, 
    start_date=datetime(2024, 6, 25),
    catchup=False,
    tags=['core', 'img_build'],
)
def DAG_image_build_REST():
    
    user = "{{ dag_run.conf.get('user') }}"
    password = "{{ dag_run.conf.get('password') }}"
    endpoint = "{{ dag_run.conf.get('endpoint') }}"
    requirements = "{{ dag_run.conf.get('requirements') }}"
    python_version = "{{ dag_run.conf.get('python_version') }}"
    use_gpu = "{{ dag_run.conf.get('use_gpu') }}"
    # print(requirements, user, password, endpoint)

    env_vars={
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

    volume_mount = k8s.V1VolumeMount(
        name="dag-dependencies", mount_path="/git"
    )

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

    path = '/git/Img_build_rest/docker'

    image_build_task = KubernetesPodOperator(
        task_id='image_build',
        name='image_build',
        namespace='airflow',
        image='gcr.io/kaniko-project/executor:latest',
        env_vars=env_vars,
        init_containers=[init_container],
        volumes=[volume],
        volume_mounts=[volume_mount],
        cmds=["/kaniko/executor"],
        arguments=[
            f"--dockerfile={path}/Dockerfile",
            f"--context={path}",
            f"--destination={endpoint}",
            f"--build-arg=PYTHON_VERSION={python_version}",
            f"--build-arg=DOCKER_USERNAME={user}",
            f"--build-arg=DOCKER_PASSWORD={password}"
        ]
    )

# Call the DAG 
DAG_image_build_REST()