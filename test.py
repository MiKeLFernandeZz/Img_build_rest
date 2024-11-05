import mlflow
import mlflow.pyfunc
import os

mlflow.set_tracking_uri("http://34.250.205.215:30005")

# Define el URI del artifact
artifact_uri = "mlflow-artifacts:/62/53c5fd68b9814b9aa2321ae007c82a29/artifacts"

# Descarga los artefactos a una ruta local
local_path = mlflow.artifacts.download_artifacts(artifact_uri, dst_path=".")
print(f"Artefactos descargados en: {local_path}")

for root, dirs, files in os.walk(local_path):
    for file in files:
        if file.startswith("model"):
            print(f"Encontrado archivo model.pkl en: {root}")
            os.rename(os.path.join(root, file), os.path.join(local_path + '/model', file))