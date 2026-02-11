#!/bin/bash
set -euo pipefail

# Converged Analytics Demo Stack Orchestration Script
# This script starts all components in the correct order with health checks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/demo-config.toml"

# Component directories
CATALOG_DIR="$PROJECT_ROOT/catalog"
TRANSACTIONAL_DB_DIR="$PROJECT_ROOT/transactional-db"
SPARK_DIR="$PROJECT_ROOT/spark"
ANALYTICS_DB_DIR="$PROJECT_ROOT/analytics-db"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_step() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $*${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking Prerequisites"

    # Check docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker."
        exit 1
    fi
    log_info "✓ Docker found: $(docker --version)"

    # Check docker-compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose not found. Please install docker-compose."
        exit 1
    fi
    log_info "✓ docker-compose found: $(docker-compose --version)"

    # Check config file
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    log_info "✓ Configuration file found: $CONFIG_FILE"

    # Check .env files
    for dir in "$TRANSACTIONAL_DB_DIR" "$ANALYTICS_DB_DIR"; do
        if [ ! -f "$dir/.env" ]; then
            log_warn "Missing .env file in $(basename "$dir")/"
            log_warn "Copy .env.example to .env and set EDB_SUBSCRIPTION_TOKEN"
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    done
}

# Wait for service to be healthy
wait_for_service() {
    local service_name="$1"
    local max_wait="${2:-300}"  # Default 5 minutes
    local interval=5
    local elapsed=0

    log_info "Waiting for $service_name to be healthy..."

    while [ $elapsed -lt $max_wait ]; do
        if docker inspect --format='{{.State.Health.Status}}' "$service_name" 2>/dev/null | grep -q "healthy"; then
            log_info "✓ $service_name is healthy"
            return 0
        fi

        # Check if container is running
        if ! docker ps --format '{{.Names}}' | grep -q "^${service_name}$"; then
            log_error "$service_name is not running"
            return 1
        fi

        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done

    echo
    log_error "$service_name did not become healthy within ${max_wait}s"
    return 1
}

# Wait for port to be available
wait_for_port() {
    local host="$1"
    local port="$2"
    local max_wait="${3:-60}"
    local interval=2
    local elapsed=0

    log_info "Waiting for $host:$port to be available..."

    while [ $elapsed -lt $max_wait ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log_info "✓ $host:$port is available"
            return 0
        fi

        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done

    echo
    log_error "$host:$port did not become available within ${max_wait}s"
    return 1
}

# Start catalog component
start_catalog() {
    log_step "Starting Catalog Component (Lakekeeper + MinIO)"

    cd "$CATALOG_DIR"

    log_info "Starting MinIO and Lakekeeper..."
    docker-compose up -d

    # Wait for services
    wait_for_service "minio" || exit 1
    wait_for_service "lakekeeper" || exit 1

    log_info "✓ Catalog component started successfully"
}

# Start transactional database component
start_transactional_db() {
    log_step "Starting Transactional Database (PGD + PGAA)"

    cd "$TRANSACTIONAL_DB_DIR"

    log_info "Building and starting PGD..."
    docker-compose up -d --build

    # Wait for service
    wait_for_service "pgd" 180 || exit 1

    # Additional check for database readiness
    log_info "Verifying database is ready..."
    sleep 10
    if docker exec pgd psql -U postgres -d demo -c '\q' &>/dev/null; then
        log_info "✓ PGD database is ready"
    else
        log_error "PGD database is not responding"
        exit 1
    fi

    log_info "✓ Transactional database started successfully"
}

# Start Spark component
start_spark() {
    log_step "Starting Spark Cluster"

    # Spark component is WIP - skip for now
    if [ ! -d "$SPARK_DIR" ]; then
        log_warn "Spark directory not found - Spark component is WIP, skipping..."
        return 0
    fi

    cd "$SPARK_DIR"

    log_info "Building and starting Spark cluster..."
    docker-compose up -d --build

    # Wait for services
    wait_for_service "spark-master" || exit 1
    wait_for_port "localhost" 15002 120 || exit 1

    log_info "✓ Spark cluster started successfully"
}

# Start analytics database component
start_analytics_db() {
    log_step "Starting Analytics Database (WarehousePG + PGAA)"

    cd "$ANALYTICS_DB_DIR"

    log_info "Building and starting WarehousePG..."
    log_info "Note: WarehousePG initialization takes ~60 seconds"
    docker-compose up -d --build

    # Wait for service (longer timeout for WHPG initialization)
    wait_for_service "whpg" 300 || exit 1

    log_info "✓ Analytics database started successfully"
}

# Display status
show_status() {
    log_step "Deployment Status"

    echo -e "${CYAN}Component Status:${NC}"
    docker-compose -f "$CATALOG_DIR/docker-compose.yml" ps
    docker-compose -f "$TRANSACTIONAL_DB_DIR/docker-compose.yml" ps
    [ -d "$SPARK_DIR" ] && docker-compose -f "$SPARK_DIR/docker-compose.yml" ps
    docker-compose -f "$ANALYTICS_DB_DIR/docker-compose.yml" ps

    echo -e "\n${CYAN}Service Endpoints:${NC}"
    echo -e "  ${GREEN}MinIO Console:${NC}       http://localhost:9001 (admin/minioadmin)"
    echo -e "  ${GREEN}MinIO API:${NC}           http://localhost:9000"
    echo -e "  ${GREEN}Lakekeeper API:${NC}      http://localhost:8181"
    echo -e "  ${GREEN}PGD Database:${NC}        localhost:7432 (postgres/secret)"
    if [ -d "$SPARK_DIR" ]; then
        echo -e "  ${GREEN}Spark Master UI:${NC}     http://localhost:8080"
        echo -e "  ${GREEN}Spark Connect:${NC}       sc://localhost:15002"
        echo -e "  ${GREEN}Spark App UI:${NC}        http://localhost:4040"
    fi
    echo -e "  ${GREEN}WarehousePG Database:${NC} localhost:5432 (gpadmin/password)"

    echo -e "\n${CYAN}Next Steps:${NC}"
    echo -e "  1. Validate configuration: ${YELLOW}python3 scripts/config_validator.py${NC}"
    echo -e "  2. Generate demo data:     ${YELLOW}python3 scripts/generate_data.py --all${NC}"
    echo -e "  3. Run example queries:    ${YELLOW}python3 scripts/query_examples.py --all${NC}"
}

# Stop all components
stop_all() {
    log_step "Stopping All Components"

    log_info "Stopping analytics database..."
    cd "$ANALYTICS_DB_DIR" && docker-compose down

    log_info "Stopping Spark cluster..."
    [ -d "$SPARK_DIR" ] && cd "$SPARK_DIR" && docker-compose down || log_warn "Spark directory not found, skipping..."

    log_info "Stopping transactional database..."
    cd "$TRANSACTIONAL_DB_DIR" && docker-compose down

    log_info "Stopping catalog..."
    cd "$CATALOG_DIR" && docker-compose down

    log_info "✓ All components stopped"
}

# Main function
main() {
    local action="${1:-start}"

    case "$action" in
        start)
            log_step "Converged Analytics Demo Stack Startup"
            check_prerequisites
            start_catalog
            start_transactional_db
            start_spark
            start_analytics_db
            show_status
            log_info "✓ All components started successfully!"
            ;;
        stop)
            stop_all
            ;;
        restart)
            stop_all
            sleep 5
            main start
            ;;
        status)
            show_status
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status}"
            echo ""
            echo "Commands:"
            echo "  start    - Start all components in order"
            echo "  stop     - Stop all components"
            echo "  restart  - Stop and start all components"
            echo "  status   - Show component status and endpoints"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
