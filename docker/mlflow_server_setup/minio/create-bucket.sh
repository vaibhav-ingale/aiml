#!/bin/bash
set -e

echo "Waiting for MinIO to be ready..."
until mc alias set minioserver http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}; do
  echo "MinIO is unavailable - sleeping"
  sleep 1
done

echo "MinIO is up - creating bucket"
# Create the MLFlow bucket if it doesn't exist
mc mb minioserver/mlflow --ignore-existing

# Set public read policy for the bucket (optional, for easier access)
mc anonymous set download minioserver/mlflow

echo "Bucket setup complete"
