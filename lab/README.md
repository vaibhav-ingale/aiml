# Unified ML & Data Platform

A complete Docker-based development environment combining **MLflow** for ML experiment tracking and **Apache Spark** for distributed data processing, with integrated **Jupyter Lab** notebooks, **MinIO** object storage, and **pgAdmin** database management.

## 🏗️ Architecture

This unified platform integrates the following services:

### Machine Learning & Database
- **MLflow** - Experiment tracking, model registry, and deployment
- **PostgreSQL** - MLflow backend database
- **pgAdmin** - Web-based PostgreSQL administration

### Distributed Data Processing
- **Spark Master** - Cluster manager and coordinator
- **Spark Workers** - Scalable compute nodes
- **Spark History Server** - Job history and monitoring

### Development & Storage
- **Jupyter Lab** - Interactive notebooks with PySpark and MLflow integration
- **MinIO** - S3-compatible object storage for artifacts and data
- **Nginx** - Reverse proxy for all services

## 📁 Directory Structure

```
lab/
├── docker-compose.yaml       # Main orchestration file
├── .env                      # Environment variables
├── .env.example              # Example environment file
├── Makefile                  # Service management commands
├── README.md                 # This file
├── QUICKSTART.md             # Quick start guide
├── spark-defaults.conf       # Spark configuration (shared)
│
├── nginx/                    # Nginx reverse proxy
│   ├── nginx.conf           # Nginx configuration
│   └── index.html           # Dashboard landing page
│
├── postgres/                 # PostgreSQL database
│   └── init.sql             # Database initialization
│
├── pgadmin/                  # PostgreSQL web UI
│   └── servers.json         # Pre-configured DB connections
│
├── minio/                    # Object storage
│   └── create-bucket.sh     # Bucket initialization script
│
├── mlflow/                   # MLflow tracking server
│   ├── Dockerfile           # MLflow custom image
│   └── requirements.txt     # Python dependencies
│
├── jupyter/                  # Jupyter Lab
│   └── Dockerfile.jupyter   # Jupyter + PySpark image
│
└── shared/                   # Shared data volumes
    ├── data/                # Datasets and files
    ├── notebooks/           # Jupyter notebooks
    ├── spark-logs/          # Spark event logs
    └── minio-data/          # MinIO storage (optional)
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM recommended
- Ports 80, 443, 5432, 7077, 9000-9001 available

### 1. Navigate to Lab Directory

```bash
cd /path/to/docker/lab
```

### 2. Configure Hosts

Add these entries to `/etc/hosts`:

```bash
# Option 1: Manual
sudo nano /etc/hosts

# Add these lines:
127.0.0.1 local.lab
127.0.0.1 mlflow.lab
127.0.0.1 pgadmin.lab
127.0.0.1 minio-console.lab
127.0.0.1 minio-api.lab
127.0.0.1 spark-master.lab
127.0.0.1 spark-history.lab
127.0.0.1 spark-jupyter.lab

# Option 2: Using Makefile (macOS/Linux)
sudo make add-hosts
```

### 3. Start Services

```bash
# Start all services
make up

# Or manually with docker-compose
docker-compose up -d
```

### 4. Access the Platform

Open your browser and navigate to: **http://local.lab**

This dashboard provides links to all services.

## 📦 Services & URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://local.lab | Main landing page |
| **MLflow** | http://mlflow.lab | ML experiment tracking |
| **pgAdmin** | http://pgadmin.lab | PostgreSQL management |
| **Spark Master** | http://spark-master.lab | Cluster management UI |
| **Spark History** | http://spark-history.lab | Job history & metrics |
| **Jupyter Lab** | http://spark-jupyter.lab | Interactive notebooks |
| **MinIO Console** | http://minio-console.lab | Object storage UI |
| **MinIO API** | http://minio-api.lab | S3 API endpoint |

## 🔐 Default Credentials

### Jupyter Lab
- **Token:** `spark123` (configured in `.env`)

### pgAdmin
- **Email:** `admin@admin.com`
- **Password:** `admin`

### MinIO
- **Username:** `minioadmin`
- **Password:** `minioadmin123`

### PostgreSQL
- **Username:** `postgres`
- **Password:** `postgres`
- **Database:** `mlflow`

## 🛠️ Makefile Commands

### Basic Operations

```bash
make help              # Display all available commands
make up                # Start all services
make down              # Stop all services
make restart           # Restart all services
make status            # Show service status
make logs              # View all logs
make urls              # Display all service URLs
```

### Service-Specific Operations

```bash
# Start individual services
make start-postgres
make start-pgadmin
make start-mlflow
make start-spark
make start-jupyter
make start-minio
make start-nginx

# Stop individual services
make stop-postgres
make stop-mlflow
make stop-spark

# Restart individual services
make restart-postgres
make restart-mlflow
make restart-spark

# View logs for specific services
make logs-postgres
make logs-pgadmin
make logs-mlflow
make logs-spark-master
make logs-jupyter
```

### Scaling

```bash
# Scale Spark workers
make scale-workers WORKERS=3
make scale-workers WORKERS=5
```

### Monitoring

```bash
make ps                # List containers
make status            # Service status
make health            # Health checks
```

### Development

```bash
# Open shell in containers
make shell-postgres
make shell-pgadmin
make shell-mlflow
make shell-spark-master
make shell-jupyter
```

### Cleanup

```bash
make clean             # Remove containers and networks
make clean-volumes     # Remove all data (WARNING!)
make prune             # Clean unused Docker resources
```

## 📓 Using Jupyter Lab

### Access Jupyter

1. Navigate to http://spark-jupyter.lab
2. Enter token: `spark123`

### PySpark Example

```python
from pyspark.sql import SparkSession

# Create Spark session
spark = SparkSession.builder \
    .appName("MyApp") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

# Create sample DataFrame
df = spark.range(1000)
df.show()

# Data is in ./shared/data/
df = spark.read.csv("/home/jovyan/data/sample.csv", header=True)
```

### MLflow Integration

```python
import mlflow

# Set tracking URI
mlflow.set_tracking_uri("http://mlflow:5001")

# Start experiment
with mlflow.start_run():
    mlflow.log_param("param1", 5)
    mlflow.log_metric("metric1", 0.85)

# View in MLflow UI: http://mlflow.lab
```

### MinIO (S3) Integration

```python
import boto3

# Configure S3 client for MinIO
s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin123'
)

# Save data
s3.upload_file('local.csv', 'bucket-name', 'data.csv')
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file to customize:

```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=mlflow

# pgAdmin
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# Jupyter
JUPYTER_TOKEN=spark123
```

### Service-Specific Configurations

- **Spark:** Edit `spark-defaults.conf` for Spark settings
- **Nginx:** Edit `nginx/nginx.conf` for proxy settings
- **MLflow:** Edit `mlflow/requirements.txt` for additional packages
- **Jupyter:** Edit `jupyter/Dockerfile.jupyter` for additional libraries
- **PostgreSQL:** Edit `postgres/init.sql` for database initialization
- **pgAdmin:** Edit `pgadmin/servers.json` for pre-configured connections

### Shared Data

All services share data through the `shared/` directory:

- `shared/data/` - Put your datasets here
- `shared/notebooks/` - Jupyter notebooks are saved here
- `shared/spark-logs/` - Spark event logs for history server

## 🔍 Troubleshooting

### Services Not Starting

```bash
# Check container status
make status

# View logs for problematic service
make logs-<service-name>

# Restart specific service
make restart-<service-name>
```

### Port Conflicts

```bash
# Check what's using the port
lsof -i :80
lsof -i :5432

# Stop conflicting service or change port in docker-compose.yaml
```

### Cannot Access Web UIs

1. Verify hosts file entries: `cat /etc/hosts | grep lab`
2. Check nginx is running: `make status`
3. Check nginx logs: `make logs-nginx`

### Data Persistence

All data is stored in Docker volumes:
- `postgres_data` - PostgreSQL database
- `pgadmin_data` - pgAdmin configuration
- `minio_data` - MinIO object storage
- `shared/` - Shared files (notebooks, data, logs)

To backup data:
```bash
# Backup volumes
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## 🔄 Updating Services

### Rebuild Single Service

```bash
# Rebuild MLflow
docker-compose build mlflow
docker-compose up -d mlflow

# Rebuild Jupyter
docker-compose build jupyter
docker-compose up -d jupyter
```

### Rebuild All Services

```bash
make rebuild
```

## 📊 Monitoring & Performance

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

### Service Health

- All services have health checks defined
- Use `make health` to see status
- Check individual logs with `make logs-<service>`

## 🤝 Adding New Services

To add a new service:

1. Create a directory in `lab/` for the service
2. Add service configuration (Dockerfile, config files)
3. Update `docker-compose.yaml` with the new service
4. Update `nginx/nginx.conf` if web UI is needed
5. Update `nginx/index.html` to add service card
6. Add service commands to `Makefile`
7. Update `.env` with any new variables

## 📝 Notes

- Each service has its own isolated directory
- Shared data is in `shared/` directory
- Spark workers are scalable (default: 1)
- MinIO is shared between MLflow and Spark
- pgAdmin comes pre-configured with PostgreSQL connection
- All services are on the same Docker network

## 🆘 Support

For issues:
1. Check logs: `make logs-<service>`
2. Verify configuration in `.env`
3. Restart service: `make restart-<service>`
4. Full restart: `make down && make up`

## 📜 License

This configuration is for development purposes. Check individual service licenses for production use.
