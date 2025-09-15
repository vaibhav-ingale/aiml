# Apache Spark 4.0.1 with Jupyter Lab Docker Setup

A Docker Compose setup for running Apache Spark 4.0.1 cluster with Jupyter Lab integration for data analysis and distributed computing.

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


### File Access

Place notebooks in `./notebooks/` and data files in `./data/` - they're automatically mounted in all containers for distributed processing.

### Features

- **Auto-restart**: All containers restart automatically if they crash
- **Shared volumes**: Files accessible across all Spark workers
- **Hostname resolution**: UI links work properly with container hostnames

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

## TODO:
1. check domains are correctly mapped or we can just leave them with the .lab domain name.
2. can not read/write from minio
3. use jupyter 6.x version and make sure we can install jupyter notebook extentions
4. install autocomplete extention may be : jupyter-tabnine, cell excecution time.
5. port and install extention for https://krishnan-r.github.io/sparkmonitor/


