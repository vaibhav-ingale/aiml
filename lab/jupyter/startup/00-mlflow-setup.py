"""
MLflow Auto-Configuration for Jupyter
This script runs automatically when the IPython kernel starts.
"""

import os

# Auto-import MLflow
try:
    import mlflow

    # Set tracking URI from environment or use default
    tracking_uri = os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow.lab')
    mlflow.set_tracking_uri(tracking_uri)

    print(f"✅ MLflow tracking URI: {tracking_uri}")
    print(f"📊 MLflow version: {mlflow.__version__}")

    # Set default experiment if desired
    # mlflow.set_experiment("default")

except ImportError:
    print("⚠️  MLflow not installed")
except Exception as e:
    print(f"⚠️  MLflow setup error: {e}")
