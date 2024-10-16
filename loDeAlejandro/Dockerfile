# Use an official Python runtime as a parent image
FROM python:3.9-slim
 
# Set the working directory in the container
# WORKDIR /app
WORKDIR /code
 
# Copy the current directory contents into the container at /app
# COPY . /app
COPY ./requirements.txt /code/requirements.txt
 
# Install dependencies from requirements.txt
# COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt
 
# Copy the app directory into the container at /app
COPY ./app /code/app
 
# Set the MLflow tracking URI as an environment variable
ENV MLFLOW_TRACKING_URI=http://34.250.205.215:5000
 
# Download the MLflow model during the Docker build
RUN mlflow models download -m "models:/XLNet_model/3" -d /code/app/models
 
# Expose port 8000 for the FastAPI app
# EXPOSE 8000
 
# Run the FastAPI app with Uvicorn or FastAPI's serve option
CMD ["fastapi", "run", "app/main.py", "--port", "80"]