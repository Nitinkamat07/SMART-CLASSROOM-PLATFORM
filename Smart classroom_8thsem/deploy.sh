#!/bin/bash

# Smart Classroom Management System Deployment Script
# This script automates the deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="smart-classroom"
ENVIRONMENT=${1:-development}
AWS_REGION=${AWS_REGION:-us-east-1}

echo -e "${BLUE}🎓 Smart Classroom Management System Deployment${NC}"
echo -e "${BLUE}================================================${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    print_status "Prerequisites check completed ✓"
}

# Setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."
    
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/classroom_management_db
REDIS_URL=redis://localhost:6379/0

# Flask Configuration
FLASK_ENV=${ENVIRONMENT}
SECRET_KEY=$(openssl rand -hex 32)

# AWS Configuration (Optional - for production)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=${AWS_REGION}
S3_BUCKET=your_s3_bucket_here

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
BCRYPT_LOG_ROUNDS=12

# Monitoring
ENABLE_MONITORING=true
EOF
        print_status ".env file created. Please update with your actual values."
    else
        print_status ".env file already exists."
    fi
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_status "Python dependencies installed ✓"
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Start PostgreSQL container if not running
    if ! docker ps | grep -q classroom_db; then
        print_status "Starting PostgreSQL container..."
        docker-compose up -d db
        
        # Wait for database to be ready
        print_status "Waiting for database to be ready..."
        sleep 10
    fi
    
    # Run database migrations
    print_status "Running database schema..."
    docker-compose exec -T db psql -U postgres -d classroom_management_db -f /docker-entrypoint-initdb.d/schema.sql || true
    
    print_status "Database setup completed ✓"
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    case $ENVIRONMENT in
        "development")
            docker-compose up -d
            ;;
        "production")
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
            ;;
        *)
            print_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    print_status "Services started ✓"
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    source venv/bin/activate
    
    # Create test database
    export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/classroom_test_db"
    
    # Run unit tests
    python -m pytest tests/ -v --cov=backend --cov-report=html
    
    print_status "Tests completed ✓"
}

# Deploy to AWS (production only)
deploy_aws() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return
    fi
    
    print_status "Deploying to AWS..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Deploy CloudFormation stack
    print_status "Deploying CloudFormation stack..."
    aws cloudformation deploy \
        --template-file deployment/cloudformation.yaml \
        --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
        --parameter-overrides \
            Environment=${ENVIRONMENT} \
            KeyName=${AWS_KEY_NAME:-default} \
            DBPassword=${DB_PASSWORD:-$(openssl rand -base64 32)} \
        --capabilities CAPABILITY_IAM \
        --region ${AWS_REGION}
    
    # Get stack outputs
    LOAD_BALANCER_URL=$(aws cloudformation describe-stacks \
        --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
        --output text \
        --region ${AWS_REGION})
    
    print_status "Application deployed to: ${LOAD_BALANCER_URL}"
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:5000/health > /dev/null 2>&1; then
            print_status "Application is healthy ✓"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - waiting for application..."
        sleep 5
        ((attempt++))
    done
    
    print_error "Health check failed after $max_attempts attempts"
    return 1
}

# Show deployment information
show_info() {
    print_status "Deployment Information:"
    echo -e "${BLUE}========================${NC}"
    echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
    echo -e "Application URL: ${YELLOW}http://localhost:5000${NC}"
    echo -e "Admin Panel: ${YELLOW}http://localhost:5000/dashboard/admin${NC}"
    echo -e "Grafana Dashboard: ${YELLOW}http://localhost:3000${NC} (admin/admin123)"
    echo -e "Prometheus: ${YELLOW}http://localhost:9090${NC}"
    echo ""
    echo -e "${GREEN}Default Login Credentials:${NC}"
    echo -e "Admin: ${YELLOW}admin / admin123${NC}"
    echo -e "Faculty: ${YELLOW}faculty / faculty123${NC}"
    echo -e "Student: ${YELLOW}student / student123${NC}"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "View logs: ${YELLOW}docker-compose logs -f${NC}"
    echo -e "Stop services: ${YELLOW}docker-compose down${NC}"
    echo -e "Restart services: ${YELLOW}docker-compose restart${NC}"
    echo -e "Update application: ${YELLOW}docker-compose up -d --build${NC}"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    docker-compose down
    docker system prune -f
    print_status "Cleanup completed ✓"
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            setup_environment
            install_dependencies
            setup_database
            start_services
            health_check
            deploy_aws
            show_info
            ;;
        "test")
            check_prerequisites
            install_dependencies
            setup_database
            run_tests
            ;;
        "cleanup")
            cleanup
            ;;
        "info")
            show_info
            ;;
        *)
            echo "Usage: $0 {deploy|test|cleanup|info} [environment]"
            echo "Environments: development, production"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"