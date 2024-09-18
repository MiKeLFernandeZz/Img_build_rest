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
    print(requirements, user, password, endpoint)

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
        env_vars=env_vars
    )
    def image_build_task():
        import logging
        import os
        from kaniko import Kaniko, KanikoSnapshotMode
        import re

        path = '/git/Img_build_rest/docker'
        user = os.getenv('user')
        password = os.getenv('pass')
        endpoint = os.getenv("endpoint") # 'registry-docker-registry.registry.svc.cluster.local:5001/mfernandezlabastida/engine:1.0'
        requirements = os.getenv("requirements")
        python_version = os.getenv("python_version")

        # Verificar si los paquetes 'mlflow', 'redis' y 'psycopg2-binary==2.9.1' están en la cadena de requirements
        # if 'mlflow' not in requirements:
        #     requirements += 'mlflow\n'
        # if 'redis' not in requirements:
        #     requirements += 'redis\n'
        # if 'psycopg2-binary==2.9.1' not in requirements:
        #     requirements += 'psycopg2-binary==2.9.1\n'

        print(f"Requirements: {requirements}")

        # Modificar la version de Python del Dockerfile
        if python_version:
            with open(f'{path}/Dockerfile', 'r') as archivo:
                lineas = archivo.readlines()

            # Modificar la línea que contiene el FROM
            with open(f'{path}/Dockerfile', 'w') as archivo:
                for linea in lineas:
                    if linea.startswith('FROM python:'):
                        # Reemplazar la versión de Python
                        archivo.write(f'FROM python:{python_version}\n')
                    else:
                        archivo.write(linea)


        # Guardar el requirements.txt en la carpeta del Dockerfile
        lineas_sanitizadas = []
    
        for linea in requirements.splitlines():
            # Elimina espacios al inicio y final de cada línea
            linea = linea.strip()
            
            # Usa una expresión regular para eliminar caracteres no permitidos
            linea_sanitizada = re.sub(r'[^a-zA-Z0-9_\-\.==]', '', linea)
            
            # Añade la línea sanitizada a la lista si no está vacía
            if linea_sanitizada:
                lineas_sanitizadas.append(linea_sanitizada)

        requirements = '\n'.join(lineas_sanitizadas)

        os.makedirs(os.path.dirname(f'{path}/requirements.txt'), exist_ok=True)

        with open(f'{path}/requirements.txt', 'w') as f:
            f.write(requirements + '\n')

        # Construir y subir la imagen
        logging.warning("Building and pushing image")
        kaniko = Kaniko()
        if(user and password):
            kaniko.build(
                dockerfile=f'{path}/Dockerfile',
                context=path,
                destination=endpoint,
                snapshot_mode=KanikoSnapshotMode.full,
                registry_username=user,
                registry_password=password,
            )
        else:
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