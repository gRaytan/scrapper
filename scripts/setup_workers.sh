#!/bin/bash
# Comprehensive worker setup and management script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Log file
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
WORKER_LOG="$LOG_DIR/celery_worker.log"
BEAT_LOG="$LOG_DIR/celery_beat.log"

# PID files
PID_DIR="$PROJECT_ROOT/tmp"
mkdir -p "$PID_DIR"
WORKER_PID="$PID_DIR/celery_worker.pid"
BEAT_PID="$PID_DIR/celery_beat.pid"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Redis is running
check_redis() {
    print_header "Checking Redis"
    
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is running"
        return 0
    else
        print_error "Redis is not running"
        print_info "Starting Redis with Docker..."
        
        # Check if container exists
        if docker ps -a --format '{{.Names}}' | grep -q "^scraper-redis$"; then
            print_info "Redis container exists, starting it..."
            docker start scraper-redis
        else
            print_info "Creating new Redis container..."
            docker run -d -p 6379:6379 --name scraper-redis redis:7-alpine
        fi
        
        # Wait for Redis to be ready
        sleep 2
        
        if redis-cli ping > /dev/null 2>&1; then
            print_success "Redis started successfully"
            return 0
        else
            print_error "Failed to start Redis"
            return 1
        fi
    fi
}

# Check if PostgreSQL is running
check_postgres() {
    print_header "Checking PostgreSQL"
    
    if psql -d job_scraper_dev -c "SELECT 1" > /dev/null 2>&1; then
        print_success "PostgreSQL is running and database is accessible"
        return 0
    else
        print_error "PostgreSQL database 'job_scraper_dev' is not accessible"
        print_warning "Please ensure PostgreSQL is running and database exists"
        return 1
    fi
}

# Check if virtual environment is activated
check_venv() {
    print_header "Checking Virtual Environment"
    
    if [ -d ".venv" ]; then
        print_success "Virtual environment found at .venv"
        
        # Check if activated
        if [ -z "$VIRTUAL_ENV" ]; then
            print_warning "Virtual environment not activated"
            print_info "Activating virtual environment..."
            source .venv/bin/activate
        fi
        
        print_success "Virtual environment activated"
        return 0
    else
        print_error "Virtual environment not found"
        print_info "Please create virtual environment: python3 -m venv .venv"
        return 1
    fi
}

# Check if Celery is installed
check_celery() {
    print_header "Checking Celery Installation"
    
    if python -c "import celery" 2>/dev/null; then
        CELERY_VERSION=$(python -c "import celery; print(celery.__version__)")
        print_success "Celery is installed (version $CELERY_VERSION)"
        return 0
    else
        print_error "Celery is not installed"
        print_info "Installing Celery..."
        pip install celery redis
        print_success "Celery installed"
        return 0
    fi
}

# Stop workers
stop_workers() {
    print_header "Stopping Workers"
    
    # Stop worker
    if [ -f "$WORKER_PID" ]; then
        WORKER_PID_NUM=$(cat "$WORKER_PID")
        if ps -p "$WORKER_PID_NUM" > /dev/null 2>&1; then
            print_info "Stopping Celery worker (PID: $WORKER_PID_NUM)..."
            kill "$WORKER_PID_NUM"
            sleep 2
            
            # Force kill if still running
            if ps -p "$WORKER_PID_NUM" > /dev/null 2>&1; then
                print_warning "Force killing worker..."
                kill -9 "$WORKER_PID_NUM"
            fi
            
            rm -f "$WORKER_PID"
            print_success "Worker stopped"
        else
            print_warning "Worker PID file exists but process not running"
            rm -f "$WORKER_PID"
        fi
    else
        # Try to find and kill any running celery workers
        pkill -f "celery.*worker" && print_success "Stopped running workers" || print_info "No workers running"
    fi
    
    # Stop beat
    if [ -f "$BEAT_PID" ]; then
        BEAT_PID_NUM=$(cat "$BEAT_PID")
        if ps -p "$BEAT_PID_NUM" > /dev/null 2>&1; then
            print_info "Stopping Celery beat (PID: $BEAT_PID_NUM)..."
            kill "$BEAT_PID_NUM"
            sleep 2
            
            # Force kill if still running
            if ps -p "$BEAT_PID_NUM" > /dev/null 2>&1; then
                print_warning "Force killing beat..."
                kill -9 "$BEAT_PID_NUM"
            fi
            
            rm -f "$BEAT_PID"
            print_success "Beat stopped"
        else
            print_warning "Beat PID file exists but process not running"
            rm -f "$BEAT_PID"
        fi
    else
        # Try to find and kill any running celery beat
        pkill -f "celery.*beat" && print_success "Stopped running beat" || print_info "No beat running"
    fi
    
    # Clean up beat schedule file
    rm -f /tmp/celerybeat-schedule
}

# Start worker
start_worker() {
    print_header "Starting Celery Worker"
    
    # Set Python path
    export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"
    
    # Start worker in background
    nohup python -m celery -A src.workers.celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        --max-tasks-per-child=50 \
        --time-limit=3600 \
        --soft-time-limit=3300 \
        --pool=prefork \
        --queues=celery \
        --hostname=worker@%h \
        --pidfile="$WORKER_PID" \
        > "$WORKER_LOG" 2>&1 &
    
    WORKER_PID_NUM=$!
    echo "$WORKER_PID_NUM" > "$WORKER_PID"
    
    # Wait a bit and check if it's running
    sleep 3
    
    if ps -p "$WORKER_PID_NUM" > /dev/null 2>&1; then
        print_success "Celery worker started (PID: $WORKER_PID_NUM)"
        print_info "Log file: $WORKER_LOG"
        return 0
    else
        print_error "Failed to start Celery worker"
        print_info "Check log file: $WORKER_LOG"
        return 1
    fi
}

# Start beat
start_beat() {
    print_header "Starting Celery Beat"
    
    # Set Python path
    export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"
    
    # Start beat in background
    nohup python -m celery -A src.workers.celery_app beat \
        --loglevel=info \
        --scheduler=celery.beat:PersistentScheduler \
        --schedule=/tmp/celerybeat-schedule \
        --pidfile="$BEAT_PID" \
        > "$BEAT_LOG" 2>&1 &
    
    BEAT_PID_NUM=$!
    echo "$BEAT_PID_NUM" > "$BEAT_PID"
    
    # Wait a bit and check if it's running
    sleep 3
    
    if ps -p "$BEAT_PID_NUM" > /dev/null 2>&1; then
        print_success "Celery beat started (PID: $BEAT_PID_NUM)"
        print_info "Log file: $BEAT_LOG"
        return 0
    else
        print_error "Failed to start Celery beat"
        print_info "Check log file: $BEAT_LOG"
        return 1
    fi
}

# Check worker status
check_status() {
    print_header "Worker Status"
    
    # Check worker
    if [ -f "$WORKER_PID" ]; then
        WORKER_PID_NUM=$(cat "$WORKER_PID")
        if ps -p "$WORKER_PID_NUM" > /dev/null 2>&1; then
            print_success "Celery worker is running (PID: $WORKER_PID_NUM)"
        else
            print_error "Celery worker is not running (stale PID file)"
        fi
    else
        print_error "Celery worker is not running"
    fi
    
    # Check beat
    if [ -f "$BEAT_PID" ]; then
        BEAT_PID_NUM=$(cat "$BEAT_PID")
        if ps -p "$BEAT_PID_NUM" > /dev/null 2>&1; then
            print_success "Celery beat is running (PID: $BEAT_PID_NUM)"
        else
            print_error "Celery beat is not running (stale PID file)"
        fi
    else
        print_error "Celery beat is not running"
    fi
    
    # Check Redis
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is running"
    else
        print_error "Redis is not running"
    fi
}

# Show logs
show_logs() {
    print_header "Recent Logs"
    
    if [ -f "$WORKER_LOG" ]; then
        echo -e "\n${BLUE}=== Worker Log (last 20 lines) ===${NC}"
        tail -n 20 "$WORKER_LOG"
    fi
    
    if [ -f "$BEAT_LOG" ]; then
        echo -e "\n${BLUE}=== Beat Log (last 20 lines) ===${NC}"
        tail -n 20 "$BEAT_LOG"
    fi
}

# Main command handler
case "${1:-start}" in
    start)
        print_header "Starting Worker Infrastructure"
        check_venv || exit 1
        check_redis || exit 1
        check_postgres || exit 1
        check_celery || exit 1
        stop_workers
        start_worker || exit 1
        start_beat || exit 1
        echo ""
        check_status
        ;;
    
    stop)
        stop_workers
        ;;
    
    restart)
        stop_workers
        sleep 2
        check_venv || exit 1
        start_worker || exit 1
        start_beat || exit 1
        echo ""
        check_status
        ;;
    
    status)
        check_status
        ;;
    
    logs)
        show_logs
        ;;
    
    tail)
        print_info "Tailing worker log (Ctrl+C to exit)..."
        tail -f "$WORKER_LOG"
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|tail}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Redis, Celery worker, and Celery beat"
        echo "  stop    - Stop Celery worker and beat"
        echo "  restart - Restart Celery worker and beat"
        echo "  status  - Check status of all components"
        echo "  logs    - Show recent logs"
        echo "  tail    - Tail worker log in real-time"
        exit 1
        ;;
esac

