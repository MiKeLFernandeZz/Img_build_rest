import mlflow
from mlflow.tracking import MlflowClient
import os

# Set the tracking URI to the remote server
MLFLOW_TRACKING_URI = 'http://34.250.205.215:30005'  # os.environ["MLFLOW_ENDPOINT"]
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

def download_model(model_name, dst_path='./model'):
    """
    Downloads a specific model version from MLflow to a specified directory.

    Parameters:
    - model_name (str): The name of the model in MLflow.
    - dst_path (str): The directory path to download the model.

    Returns:
    - bool: True if the model was downloaded successfully, False otherwise.
    """
    client = MlflowClient()
    
    # Get the latest version of the model in the specified stage
    latest_versions = client.get_latest_versions(model_name, stages=['Production'])
    print(latest_versions)
    
    # Check if any models were found in Production
    if not latest_versions:
        print(f"No models found in stage: {'Production'}")
        return False
    
    # Get the latest version of the model
    latest_model = latest_versions[0]
    latest_version = int(latest_model.version)
    try:
        # Create the download directory if it doesn't exist
        os.makedirs(dst_path, exist_ok=True)
        
        # Download the model
        model_uri = f"models:/{model_name}/{latest_version}"
        mlflow.pyfunc.load_model(model_uri, dst_path=dst_path)
        
        print(f"Model version {latest_version} downloaded to {dst_path}")
        return True
    except Exception as e:
        print(f"Failed to download model version {latest_version}: {e}")
        return False

def check_and_download_new_model(current_version, model_name, model_stage='Production', download_path='./model'):
    """
    Checks if there is a new model version in production in MLflow and downloads it if the version is newer than the current one.

    Parameters:
    - current_version (int): The current version of the model.
    - model_name (str): The name of the model in MLflow.
    - model_stage (str): The stage of the model to check (default is 'Production').
    - download_path (str): The directory path to download the new model.

    Returns:
    - bool: True if a new model version was downloaded, False otherwise.
    """
    client = MlflowClient()
    
    # Get the latest version of the model in the specified stage
    latest_versions = client.get_latest_versions(model_name, stages=[model_stage])
    
    if not latest_versions:
        print(f"No models found in stage: {model_stage}")
        return False
    
    latest_model = latest_versions[0]
    latest_version = int(latest_model.version)
    
    if latest_version > current_version:
        print(f"New model version {latest_version} found. Current version: {current_version}. Downloading...")
        
        # Create the download directory if it doesn't exist
        os.makedirs(download_path, exist_ok=True)
        
        # Download the new model
        model_uri = f"models:/{model_name}/{latest_version}"
        mlflow.pyfunc.load_model(model_uri, dst_path=download_path)
        
        print(f"Model version {latest_version} downloaded to {download_path}")
        return True
    else:
        print(f"Current model version ({current_version}) is up-to-date.")
        return False
    
download_model("ElasticNet(alpha=0.5, l1_ratio=0.5)", dst_path='./model')