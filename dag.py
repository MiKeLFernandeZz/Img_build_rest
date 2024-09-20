from datetime import datetime
from airflow.decorators import dag, task
from kubernetes.client import models as k8s
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

    @task.kubernetes(
        image='mfernandezlabastida/kaniko:1.0',
        name='image_build',
        task_id='image_build',
        namespace='airflow',
        init_containers=[init_container],
        volumes=[volume],
        volume_mounts=[volume_mount],
        do_xcom_push=True,
        container_resources=k8s.V1ResourceRequirements(
            requests={'cpu': '1'},
            limits={'cpu': '1.5'}
        ),
        env_vars=env_vars,
        get_logs=True
    )
    def image_build_task():
        import logging
        import os
        from kaniko import Kaniko, KanikoSnapshotMode
        import time

        user = os.getenv('user')
        password = os.getenv('pass')
        endpoint = os.getenv("endpoint") # 'registry-docker-registry.registry.svc.cluster.local:5001/mfernandezlabastida/engine:1.0'
        requirements = os.getenv("requirements")
        python_version = os.getenv("python_version")
        use_gpu = os.getenv("use_gpu")
        required_packages = ['mlflow', 'redis', 'psycopg2-binary']

        path = '/git/Img_build_rest/docker'

        # Verificar si se debe usar GPU
        if use_gpu == 'true':
            logging.warning("Using GPU")
            path = '/git/Img_build_rest/docker_gpus'

        # Verificar si las dependencias se encuentran en el requirements.txt
        # requirements_list = requirements.split()
        # for package in required_packages:
        #     if package not in requirements_list:
        #         requirements_list.append(package)

        # requirements = ' '.join(requirements_list)

        logging.warning(f"Requirements: {requirements}")
        logging.warning(f"User: {user}")

        # Sustituir la versión de Python en el Dockerfile
        with open(f'{path}/Dockerfile', 'r', encoding='utf-8') as file:
            content = file.read()

        content = content.replace('{{PYTHON_VERSION}}', python_version)
        content = content.replace('{{REQUIREMENTS}}', requirements)

        with open(f'{path}/Dockerfile', 'w', encoding='utf-8') as file:
            file.write(content)

        # Modificar la version de Python del Dockerfile
        # if python_version:
        #     with open(f'{path}/Dockerfile', 'r') as archivo:
        #         lineas = archivo.readlines()

        #     # Modificar la línea que contiene el FROM
        #     with open(f'{path}/Dockerfile', 'w') as archivo:
        #         for linea in lineas:
        #             if linea.startswith('FROM python:'):
        #                 # Reemplazar la versión de Python
        #                 archivo.write(f'FROM python:{python_version}\n')
        #             if linea.startswith('RUN pip install --no-cache-dir -r'):
        #                 # Reemplazar la versión de Python
        #                 archivo.write(f'RUN pip install --no-cache-dir {requirements}\n')
        #             else:
        #                 archivo.write(linea)


        # Construir y subir la imagen
        logging.warning("Building and pushing image")
        kaniko = Kaniko()
        time.sleep(5)
        if(user and password):
            logging.warning(f"Logging with user and password")
            kaniko.build(
                dockerfile=f'{path}/Dockerfile',
                context=path,
                destination=endpoint,
                snapshot_mode=KanikoSnapshotMode.full,
                registry_username=user,
                registry_password=password,
            )
        else:
            logging.warning(f"Logging without user and password")
            kaniko.build(
                dockerfile=f'{path}/Dockerfile',
                context=path,
                destination=endpoint,
                snapshot_mode=KanikoSnapshotMode.full
            )

    # @task.kubernetes(
    #     image='mfernandezlabastida/kaniko:1.0',
    #     name='image_build_2',
    #     task_id='image_build_2',
    #     namespace='airflow',
    #     init_containers=[init_container],
    #     volumes=[volume],
    #     volume_mounts=[volume_mount],
    #     do_xcom_push=True,
    #     container_resources=k8s.V1ResourceRequirements(
    #         requests={'cpu': '0.5'},
    #         limits={'cpu': '0.8'}
    #     ),
    #     env_vars=env_vars
    # )
    # def image_build_mlflow_task(run_id):
    #     import mlflow
    #     import os
    #     import shutil
    #     import logging
    #     from kaniko import Kaniko, KanikoSnapshotMode
    #     # import sys

    #     # sys.path.insert(1, '/git/DAG_image_build')

    #     path = '/git/Img_build_rest/'

    #     try:
    #         # Obtener información del run
    #         run_info = mlflow.get_run(run_id)
    #         artifact_uri = run_info.info.artifact_uri + '/model/requirements.txt'

    #         print(f"URI de los artefactos del run: {artifact_uri}")

    #         # Descargar el artefacto requirements.txt a una carpeta temporal
    #         tmp_artifact_dir = os.path.join(path, "artifacts")
    #         mlflow.artifacts.download_artifacts(run_id=run_id, dst_path=tmp_artifact_dir, artifact_path='model/requirements.txt')

    #         # Verificar si el archivo fue descargado correctamente
    #         downloaded_file = os.path.join(tmp_artifact_dir, 'model', 'requirements.txt')
    #         print(downloaded_file)
    #         if os.path.exists(downloaded_file):
    #             # Mover el archivo descargado a la ubicación deseada
    #             shutil.move(downloaded_file, os.path.join(path, 'docker', 'requirements.txt'))
    #             print("Archivo requirements.txt movido exitosamente.")
    #         else:
    #             print(f"Error: No se pudo descargar el archivo requirements.txt desde {artifact_uri}.")
    #     except mlflow.exceptions.MlflowException as e:
    #         print(f"Error de MLflow: {e}")
    #     except FileNotFoundError:
    #         print(f"Error: No se encontró el archivo en la ruta especificada.")
    #     except PermissionError:
    #         print(f"Error: Permiso denegado para acceder al archivo o directorio.")
    #     except Exception as e:
    #         print(f"Error inesperado: {str(e)}")


    #     logging.warning("Building and pushing image")
    #     kaniko = Kaniko()
    #     kaniko.build(
    #         dockerfile=os.path.join(path, 'docker', 'Dockerfile'),
    #         context=path,
    #         destination='registry-docker-registry.registry.svc.cluster.local:5001/mfernandezlabastida/engine:1.1',
    #         snapshot_mode=KanikoSnapshotMode.full,
    #         # registry_username='username',
    #         # registry_password='password',
    #     )

    image_build_result = image_build_task()
    # image_build_mlflow_result = image_build_mlflow_task('51e9022a0c2442da9c6e7b130b56defc')
    
    # Define the order of the pipeline
    image_build_result
# Call the DAG 
DAG_image_build_REST()