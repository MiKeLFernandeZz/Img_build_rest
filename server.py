import pickle
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import os
import numpy as np

# Definir el modelo FastAPI
app = FastAPI()

# Cargar el modelo desde un archivo local
model_path = "artifacts/model/model.pkl"  # Reemplaza con la ruta a tu modelo
with open(model_path, "rb") as model_file:
    model = pickle.load(model_file)

# # Definir el esquema de entrada para las predicciones
# class PredictionInput(BaseModel):
#     # Define aquí los atributos que espera tu modelo
#     # Por ejemplo, si el modelo espera dos columnas 'feature1' y 'feature2'
#     feature1: float
#     feature2: float

@app.post("/predict")
def predict(input_data):
    # Convertir los datos de entrada a un DataFrame
    input_df = np.array([*eval(input_data).values()]).reshape(1, -1)
    
    # Realizar la predicción
    prediction = model.predict(input_df)[0]
    
    # Retornar la predicción
    return {"prediction": prediction.tolist()}

if __name__ == "__main__":
    import uvicorn
    # Iniciar el servidor FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)
