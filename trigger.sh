#!/bin/bash

# Parámetros de la solicitud
DAG_ID="DAG_image_build_REST"  # Reemplaza con el ID de tu DAG
USERNAME="airflow"  # Reemplaza con tu nombre de usuario
PASSWORD="clarus_airflow_admin_ik"  # Reemplaza con tu contraseña
BASE_URL="http://34.250.205.215:30007"  # Reemplaza con la URL de tu Airflow
REQUIREMENTS=$(awk '{printf "%s\\n", $0}' "requirements.txt")

# Valor único para esta ejecución (puede ser generado dinámicamente)
MY_VARIABLE="value_$(date +%s)"  # Valor dinámico basado en el timestamp actual

# Construye la URL para disparar el DAG
URL="${BASE_URL}/api/v1/dags/${DAG_ID}/dagRuns"

# Cuerpo de la solicitud en formato JSON, que incluye la variable en conf
POST_DATA=$(cat <<EOF
{
  "conf": {
    "user": "ikerlan",
    "password": "ikerlan",
    "endpoint": "test",
    "requirements": "$REQUIREMENTS"
  },
  "dag_run_id": "manual__$(date +%s)"
}
EOF
)

echo $POST_DATA

# Realiza la solicitud POST usando curl
response=$(curl -X POST "$URL" \
  -H "Content-Type: application/json" \
  -u "$USERNAME:$PASSWORD" \
  -d "$POST_DATA")

# Verifica la respuesta
if echo "$response" | grep -q '"dag_run_id"'; then
  echo "DAG ejecutado con éxito."
  echo "Respuesta de Airflow: $response"
else
  echo "Error al ejecutar el DAG."
  echo "Respuesta de Airflow: $response"
fi
