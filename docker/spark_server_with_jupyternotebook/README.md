# Apache Spark 4.0 with Jupyter Lab Docker Setup

A Docker Compose setup for running Apache Spark 4.0 cluster with Jupyter Lab integration for data analysis and distributed computing.

## Architecture

- **Spark Master**: Cluster coordination (port 8080)
- **Spark Workers**: 3 worker nodes (ports 8081-8083)  
- **Spark History Server**: Job history tracking (port 18080)
- **Jupyter Lab**: Interactive notebooks with PySpark (port 8888)
- **MinIO**: S3-compatible object storage (ports 9000/9001)

## Quick Start

```bash
# Start the cluster
docker-compose up -d

# Add .lab domain hostnames to /etc/hosts for custom domain access
echo -e "127.0.0.1 spark-master.lab\n127.0.0.1 spark-worker-1.lab\n127.0.0.1 spark-worker-2.lab\n127.0.0.1 spark-worker-3.lab\n127.0.0.1 spark-jupyter.lab\n127.0.0.1 spark-history-server.lab\n127.0.0.1 minio-storage.lab" | sudo tee -a /etc/hosts

# Access services via .lab domains or localhost
open http://spark-jupyter.lab:8888    # or http://localhost:8888
# Token: spark123

open http://spark-master.lab:8080     # or http://localhost:8080
open http://minio-storage.lab:9001    # or http://localhost:9001
```


### Service Access URLs

**Using .lab domains:**
- Spark Master UI: http://spark-master.lab:8080
- Spark History Server: http://spark-history-server.lab:18080
- Jupyter Lab: http://spark-jupyter.lab:8888
- Worker UIs: http://spark-worker-1.lab:8081, http://spark-worker-2.lab:8082, http://spark-worker-3.lab:8083
- MinIO Console: http://minio-storage.lab:9001
- MinIO API: http://minio-storage.lab:9000

**Using localhost (alternative):**
- All services are also accessible via localhost with their respective ports


## Services & Ports

| Service | Port | .lab Domain | Description |
|---------|------|-------------|-------------|
| Jupyter Lab | 8888 | spark-jupyter.lab | Interactive notebooks |
| Spark Master UI | 8080 | spark-master.lab | Cluster management |
| Spark Worker 1 | 8081 | spark-worker-1.lab | Worker node status |
| Spark Worker 2 | 8082 | spark-worker-2.lab | Worker node status |  
| Spark Worker 3 | 8083 | spark-worker-3.lab | Worker node status |
| History Server | 18080 | spark-history-server.lab | Job history |
| Spark Driver UI | 4040-4050 | N/A | Application monitoring |
| MinIO API | 9000 | minio-storage.lab | S3-compatible storage |
| MinIO Console | 9001 | minio-storage.lab | Storage management UI |

## Directory Structure

```
├── docker-compose.yaml    # Service definitions
├── Dockerfile.jupyter     # Custom Jupyter image
├── notebooks/             # Jupyter notebooks
├── data/                  # Shared data files
└── minio-data/           # MinIO S3 storage
```

## Configuration

- **Spark Version**: 4.0.0
- **Python Version**: 3.10
- **Worker Resources**: 2 cores, 2GB RAM each
- **Total Cluster**: 6 cores, 6GB RAM

## Usage

### PySpark in Jupyter

```python
from pyspark.sql import SparkSession

# For distributed cluster mode
spark = SparkSession.builder \
    .master("spark://spark-master:7077") \
    .appName("YourAppName") \
    .config("spark.driver.host", "spark-jupyter") \
    .config("spark.driver.bindAddress", "0.0.0.0") \
    .getOrCreate()

# For local mode (single machine)
spark = SparkSession.builder \
    .appName("YourAppName") \
    .getOrCreate()
```

### File Access

Place notebooks in `./notebooks/` and data files in `./data/` - they're automatically mounted in all containers for distributed processing.

### S3 Storage with MinIO

```python
import boto3
from minio import Minio

# MinIO credentials - use either .lab domain or container hostname
endpoint_url = 'http://minio-storage.lab:9000'  # or 'http://spark-minio:9000' 
access_key = 'minioadmin'
secret_key = 'minioadmin123'

# Using boto3 for S3 operations
s3_client = boto3.client(
    's3',
    endpoint_url=endpoint_url,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
)

# Using MinIO client
minio_client = Minio(
    'minio-storage.lab:9000',  # or 'spark-minio:9000'
    access_key=access_key,
    secret_key=secret_key,
    secure=False
)

# Reading S3 data with Spark
spark.conf.set("spark.hadoop.fs.s3a.endpoint", "http://minio-storage.lab:9000")  # or "http://spark-minio:9000"
spark.conf.set("spark.hadoop.fs.s3a.access.key", "minioadmin")
spark.conf.set("spark.hadoop.fs.s3a.secret.key", "minioadmin123")
spark.conf.set("spark.hadoop.fs.s3a.path.style.access", "true")
spark.conf.set("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

# Load data from S3
df = spark.read.csv("s3a://your-bucket/your-file.csv", header=True)
```

### Features

- **Auto-restart**: All containers restart automatically if they crash
- **Shared volumes**: Files accessible across all Spark workers
- **Hostname resolution**: UI links work properly with container hostnames
- **S3 Storage**: MinIO provides S3-compatible object storage for big data

## Stopping

```bash
docker-compose down
```

### Custom Domain Setup

Add these entries to your `/etc/hosts` file for custom `.lab` domain access:

```bash
echo -e "127.0.0.1 spark-master.lab\n127.0.0.1 spark-worker-1.lab\n127.0.0.1 spark-worker-2.lab\n127.0.0.1 spark-worker-3.lab\n127.0.0.1 spark-jupyter.lab\n127.0.0.1 spark-history-server.lab\n127.0.0.1 minio-storage.lab" | sudo tee -a /etc/hosts
```

After adding these entries, you can access all services using their `.lab` domain names instead of localhost.