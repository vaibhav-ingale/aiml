# Certificate Generation Utility

A comprehensive utility for generating SSL certificates for local development environments.

## Features

- **CA Certificate Generation**: Create your own Certificate Authority
- **Wildcard Certificates**: Generate certificates for multiple subdomains (\*.domain.com)
- **Domain-specific Certificates**: Generate certificates for specific domains
- **Organized Configuration**: Keep configurations in dedicated directories

## Quick Start

1. **Setup**: Create directory structure and sample configurations

   ```bash
   ./cert-utils.sh setup
   ```

2. **Generate CA Certificate**:

   ```bash
   ./cert-utils.sh ca
   ```

3. **Generate Wildcard Certificate**:

   ```bash
   ./cert-utils.sh wildcard configs/wildcard/lab.conf lab
   ```

4. **Generate Domain-specific Certificate**:
   ```bash
   ./cert-utils.sh domain configs/domains/mlflow.lab.conf mlflow.lab
   ```

## Directory Structure

```
├── cert-utils.sh           # Main utility script
├── configs/                # Configuration files
│   ├── ca/                # CA configurations
│   │   └── ca.conf        # Default CA config
│   ├── wildcard/          # Wildcard configurations
│   │   ├── wildcard.conf  # Default wildcard config
│   │   └── lab.conf       # Lab domain wildcard config
│   └── domains/           # Domain-specific configurations
│       ├── example.com.conf
│       ├── mlflow.lab.conf
│       └── minio-console.lab.conf
└── ssl/                   # Generated certificates
    ├── ca/                # CA certificates
    │   ├── ca-cert.pem
    │   └── ca-key.pem
    └── certs/             # Domain certificates
        ├── domain-cert.pem
        ├── domain-key.pem
        ├── mlflow.lab-cert.pem
        └── mlflow.lab-key.pem
```

## Usage Examples

### Generate CA Certificate

```bash
# Using default config
./cert-utils.sh ca

# Using custom config
./cert-utils.sh ca configs/ca/custom-ca.conf
```

### Generate Wildcard Certificate

```bash
# Generate wildcard certificate for .lab domain
./cert-utils.sh wildcard configs/wildcard/lab.conf lab-wildcard

# Using default config
./cert-utils.sh wildcard
```

### Generate Domain-specific Certificate

```bash
# Generate certificate for mlflow.lab
./cert-utils.sh domain configs/domains/mlflow.lab.conf mlflow.lab

# Generate certificate for minio-console.lab
./cert-utils.sh domain configs/domains/minio-console.lab.conf minio-console.lab
```

## Configuration Files

Configuration files use OpenSSL format and should be placed in the appropriate directories:

- **CA configs**: `configs/ca/`
- **Wildcard configs**: `configs/wildcard/`
- **Domain configs**: `configs/domains/`

### Creating New Configurations

1. Copy an existing configuration file
2. Modify the `[req_distinguished_name]` section with your details
3. Update the `[alt_names]` section with your domains
4. Save in the appropriate directory

## Trust CA Certificate

After generating the CA certificate, add it to your system's trust store:

### macOS

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ssl/ca/ca-cert.pem
```

### Linux

```bash
sudo cp ssl/ca/ca-cert.pem /usr/local/share/ca-certificates/lab-ca.crt
sudo update-ca-certificates
```

### Windows

Import `ssl/ca/ca-cert.pem` to "Trusted Root Certification Authorities" store

## Add Domains to Hosts File

Add the following to your `/etc/hosts` file:

```
127.0.0.1 lab
127.0.0.1 mlflow.lab
127.0.0.1 minio-console.lab
```

## Legacy Script

The original `generate-certs.sh` script is still available for backward compatibility but it's recommended to use the new `cert-utils.sh` for better organization and flexibility.
