#!/bin/bash

# Certificate Generation Utility
# This utility provides functions to generate:
# 1. CA certificates
# 2. Wildcard certificates
# 3. Domain-specific certificates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="$SCRIPT_DIR/ssl"
CA_DIR="$SSL_DIR/ca"
CERTS_DIR="$SSL_DIR/certs"
CONFIGS_DIR="$SCRIPT_DIR/configs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create directory structure
create_directories() {
    log_info "Creating SSL directory structure..."
    mkdir -p "$CA_DIR" "$CERTS_DIR" "$CONFIGS_DIR/ca" "$CONFIGS_DIR/wildcard" "$CONFIGS_DIR/domains"
    log_success "Directory structure created"
}

# Generate CA certificate
generate_ca() {
    local ca_config="${1:-$CONFIGS_DIR/ca/ca.conf}"
    
    # Convert to absolute path
    if [[ "$ca_config" != /* ]]; then
        ca_config="$SCRIPT_DIR/$ca_config"
    fi
    
    if [ ! -f "$ca_config" ]; then
        log_error "CA configuration file not found: $ca_config"
        log_info "Please create the CA configuration file with required settings"
        return 1
    fi
    
    log_info "Generating CA certificate..."
    cd "$CA_DIR"
    
    # Generate CA private key
    log_info "Generating CA private key..."
    openssl genrsa -out ca-key.pem 4096
    
    # Generate CA certificate
    log_info "Generating CA certificate..."
    openssl req -new -x509 -sha256 -days 3650 -key ca-key.pem -out ca-cert.pem -config "$ca_config"
    
    log_success "CA certificate generated successfully"
    log_info "CA files created:"
    log_info "  Private Key: $CA_DIR/ca-key.pem"
    log_info "  Certificate: $CA_DIR/ca-cert.pem"
}

# Generate wildcard certificate
generate_wildcard() {
    local wildcard_config="${1:-$CONFIGS_DIR/wildcard/wildcard.conf}"
    local cert_name="${2:-wildcard}"
    
    # Convert to absolute path
    if [[ "$wildcard_config" != /* ]]; then
        wildcard_config="$SCRIPT_DIR/$wildcard_config"
    fi
    
    if [ ! -f "$wildcard_config" ]; then
        log_error "Wildcard configuration file not found: $wildcard_config"
        log_info "Please create the wildcard configuration file with required settings"
        return 1
    fi
    
    if [ ! -f "$CA_DIR/ca-cert.pem" ] || [ ! -f "$CA_DIR/ca-key.pem" ]; then
        log_error "CA certificate not found. Please generate CA first using: $0 ca"
        return 1
    fi
    
    log_info "Generating wildcard certificate: $cert_name"
    cd "$CERTS_DIR"
    
    # Generate domain private key
    log_info "Generating private key..."
    openssl genrsa -out "${cert_name}-key.pem" 2048
    
    # Generate certificate signing request
    log_info "Generating certificate signing request..."
    openssl req -new -key "${cert_name}-key.pem" -out "${cert_name}.csr" -config "$wildcard_config"
    
    # Sign certificate with CA
    log_info "Signing certificate with CA..."
    openssl x509 -req -in "${cert_name}.csr" -CA "$CA_DIR/ca-cert.pem" -CAkey "$CA_DIR/ca-key.pem" -CAcreateserial -out "${cert_name}-cert.pem" -days 365 -extensions v3_req -extfile "$wildcard_config"
    
    # Clean up CSR file
    rm "${cert_name}.csr"
    
    log_success "Wildcard certificate generated successfully"
    log_info "Certificate files created:"
    log_info "  Private Key: $CERTS_DIR/${cert_name}-key.pem"
    log_info "  Certificate: $CERTS_DIR/${cert_name}-cert.pem"
}

# Generate domain-specific certificate
generate_domain() {
    local domain_config="${1}"
    local domain_name="${2}"
    
    if [ -z "$domain_config" ] || [ -z "$domain_name" ]; then
        log_error "Usage: $0 domain <config_file> <domain_name>"
        log_info "Example: $0 domain configs/domains/example.com.conf example.com"
        return 1
    fi
    
    # Convert to absolute path
    if [[ "$domain_config" != /* ]]; then
        domain_config="$SCRIPT_DIR/$domain_config"
    fi
    
    if [ ! -f "$domain_config" ]; then
        log_error "Domain configuration file not found: $domain_config"
        log_info "Please create the domain configuration file with required settings"
        return 1
    fi
    
    if [ ! -f "$CA_DIR/ca-cert.pem" ] || [ ! -f "$CA_DIR/ca-key.pem" ]; then
        log_error "CA certificate not found. Please generate CA first using: $0 ca"
        return 1
    fi
    
    log_info "Generating domain-specific certificate: $domain_name"
    cd "$CERTS_DIR"
    
    # Generate domain private key
    log_info "Generating private key..."
    openssl genrsa -out "${domain_name}-key.pem" 2048
    
    # Generate certificate signing request
    log_info "Generating certificate signing request..."
    openssl req -new -key "${domain_name}-key.pem" -out "${domain_name}.csr" -config "$domain_config"
    
    # Sign certificate with CA
    log_info "Signing certificate with CA..."
    openssl x509 -req -in "${domain_name}.csr" -CA "$CA_DIR/ca-cert.pem" -CAkey "$CA_DIR/ca-key.pem" -CAcreateserial -out "${domain_name}-cert.pem" -days 365 -extensions v3_req -extfile "$domain_config"
    
    # Clean up CSR file
    rm "${domain_name}.csr"
    
    log_success "Domain certificate generated successfully"
    log_info "Certificate files created:"
    log_info "  Private Key: $CERTS_DIR/${domain_name}-key.pem"
    log_info "  Certificate: $CERTS_DIR/${domain_name}-cert.pem"
}

# Show usage information
show_usage() {
    echo "Certificate Generation Utility"
    echo "=============================="
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  ca [config_file]                    Generate CA certificate"
    echo "  wildcard [config_file] [cert_name] Generate wildcard certificate"
    echo "  domain <config_file> <domain_name> Generate domain-specific certificate"
    echo "  setup                               Create directory structure and sample configs"
    echo "  help                                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup                                    # Create directories and sample configs"
    echo "  $0 ca                                       # Generate CA using default config"
    echo "  $0 ca configs/ca/custom-ca.conf            # Generate CA using custom config"
    echo "  $0 wildcard                                 # Generate wildcard cert using default config"
    echo "  $0 wildcard configs/wildcard/lab.conf lab  # Generate wildcard cert for .lab domain"
    echo "  $0 domain configs/domains/api.conf api     # Generate cert for api domain"
    echo ""
    echo "Configuration files should be placed in:"
    echo "  CA configs: configs/ca/"
    echo "  Wildcard configs: configs/wildcard/"
    echo "  Domain configs: configs/domains/"
}

# Create sample configuration files
create_sample_configs() {
    log_info "Creating sample configuration files..."
    
    # CA configuration
    cat > "$CONFIGS_DIR/ca/ca.conf" << 'EOF'
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = US
ST = Local
L = Local
O = Lab Environment
OU = Development
CN = Lab Root CA

[v3_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical,CA:true
keyUsage = critical,digitalSignature,cRLSign,keyCertSign
EOF

    # Wildcard configuration
    cat > "$CONFIGS_DIR/wildcard/wildcard.conf" << 'EOF'
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = Local
L = Local
O = Lab Environment
OU = Development
CN = *.lab

[v3_req]
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = *.lab
DNS.2 = lab
EOF

    # Sample domain configuration
    cat > "$CONFIGS_DIR/domains/example.com.conf" << 'EOF'
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = Local
L = Local
O = Lab Environment
OU = Development
CN = example.com

[v3_req]
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = example.com
DNS.2 = www.example.com
DNS.3 = api.example.com
EOF

    log_success "Sample configuration files created"
    log_info "Configuration files created:"
    log_info "  CA: $CONFIGS_DIR/ca/ca.conf"
    log_info "  Wildcard: $CONFIGS_DIR/wildcard/wildcard.conf"
    log_info "  Domain example: $CONFIGS_DIR/domains/example.com.conf"
}

# Setup function
setup() {
    create_directories
    create_sample_configs
    log_success "Setup completed!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Customize configuration files in the configs/ directory"
    log_info "2. Generate CA certificate: $0 ca"
    log_info "3. Generate certificates as needed"
}

# Display trust instructions
show_trust_instructions() {
    log_info ""
    log_info "To trust the CA certificate:"
    log_info "macOS: sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $CA_DIR/ca-cert.pem"
    log_info "Linux: sudo cp $CA_DIR/ca-cert.pem /usr/local/share/ca-certificates/lab-ca.crt && sudo update-ca-certificates"
    log_info "Windows: Import $CA_DIR/ca-cert.pem to 'Trusted Root Certification Authorities'"
}

# Main script logic
case "${1:-help}" in
    "ca")
        create_directories
        generate_ca "$2"
        show_trust_instructions
        ;;
    "wildcard")
        create_directories
        generate_wildcard "$2" "$3"
        ;;
    "domain")
        create_directories
        generate_domain "$2" "$3"
        ;;
    "setup")
        setup
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac