# Quick Start Guide

Get the unified ML & Data platform running in 3 minutes!

## Step 1: Add Hosts

**On macOS/Linux:**
```bash
sudo bash -c 'cat >> /etc/hosts << EOF
127.0.0.1 local.lab
127.0.0.1 mlflow.lab
127.0.0.1 minio-console.lab
127.0.0.1 minio-api.lab
127.0.0.1 spark-master.lab
127.0.0.1 spark-history.lab
127.0.0.1 spark-jupyter.lab
127.0.0.1 spark-app.lab
EOF'
```

**Or use the Makefile:**
```bash
sudo make add-hosts
```

## Step 2: Start Everything

```bash
make up
```

That's it! Wait 30-60 seconds for all services to start.

## Step 3: Access Services

Open your browser to: **http://local.lab**

Or access services directly:

| Service | URL | Credentials |
|---------|-----|------------|
| Dashboard | http://local.lab | - |
| MLflow | http://mlflow.lab | - |
| Jupyter Lab | http://spark-jupyter.lab | Token: `spark123` |
| Spark Master | http://spark-master.lab | - |
| MinIO Console | http://minio-console.lab | user: `minioadmin`, pass: `minioadmin123` |

## Quick Commands

```bash
make help              # Show all commands
make status            # Check service status
make logs              # View all logs
make down              # Stop everything
make scale-workers WORKERS=3  # Scale Spark workers
```

## Test It Out

### In Jupyter Lab (http://spark-jupyter.lab)

```python
# Test Spark
from pyspark.sql import SparkSession
spark = SparkSession.builder.master("spark://spark-master:7077").getOrCreate()
spark.range(100).count()

# Test MLflow
import mlflow
mlflow.set_tracking_uri("http://mlflow:5001")
with mlflow.start_run():
    mlflow.log_param("test", "value")
```

View your experiment at http://mlflow.lab

## Troubleshooting

**Can't access URLs?**
- Check hosts file: `cat /etc/hosts | grep lab`
- Restart: `make down && make up`

**Services not starting?**
- Check logs: `make logs`
- Check status: `make status`

**Port conflicts?**
- Find process: `lsof -i :80`
- Stop conflicting service

## Next Steps

Read the full [README.md](README.md) for:
- Detailed architecture
- All Makefile commands
- Integration examples
- Advanced configuration
