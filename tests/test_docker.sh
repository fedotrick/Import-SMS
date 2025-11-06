#!/bin/bash
# Test script for Docker deployment

set -e

echo "======================================"
echo "DOCKER DEPLOYMENT TEST"
echo "======================================"

cd "$(dirname "$0")/.."

# Check if .env exists
echo -e "\n1. Checking .env file..."
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env from .env.example"
        echo "⚠️  Please set BOT_TOKEN in .env before running the bot"
    else
        echo "✗ .env.example not found!"
        exit 1
    fi
else
    echo "✓ .env file exists"
fi

# Check Контроль directory
echo -e "\n2. Checking Контроль directory..."
if [ ! -d "Контроль" ]; then
    echo "⚠️  Контроль directory not found. Creating..."
    mkdir -p Контроль
    echo "✓ Created Контроль directory"
else
    echo "✓ Контроль directory exists"
fi

# Check if docker compose is available
echo -e "\n3. Checking Docker availability..."
if ! command -v docker &> /dev/null; then
    echo "✗ Docker is not available"
    exit 1
fi
echo "✓ Docker is available"

# Use docker compose (new syntax) or docker-compose (old syntax)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "⚠️  Docker Compose is not available, skipping build tests"
    DOCKER_COMPOSE=""
fi

if [ -n "$DOCKER_COMPOSE" ]; then
    echo "✓ Using: $DOCKER_COMPOSE"
    
    # Build Docker image
    echo -e "\n4. Building Docker image..."
    if $DOCKER_COMPOSE build; then
        echo "✓ Docker image built successfully"
    else
        echo "✗ Docker build failed"
        exit 1
    fi

    # Check Docker Compose configuration
    echo -e "\n5. Validating Docker Compose configuration..."
    if $DOCKER_COMPOSE config > /dev/null 2>&1; then
        echo "✓ Docker Compose configuration is valid"
    else
        echo "✗ Invalid Docker Compose configuration"
        exit 1
    fi
else
    echo -e "\n4. Validating Dockerfile syntax..."
    if docker build -f Dockerfile -t plavka-bot-test . > /dev/null 2>&1; then
        echo "✓ Dockerfile is valid"
    else
        echo "✗ Dockerfile has errors"
        exit 1
    fi
fi

echo -e "\n======================================"
echo "DOCKER TESTS COMPLETED"
echo "======================================"
echo ""
if [ -n "$DOCKER_COMPOSE" ]; then
    echo "To start the bot in Docker:"
    echo "  $DOCKER_COMPOSE up -d"
    echo ""
    echo "To view logs:"
    echo "  $DOCKER_COMPOSE logs -f"
    echo ""
    echo "To check health:"
    echo "  $DOCKER_COMPOSE ps"
    echo ""
    echo "To stop:"
    echo "  $DOCKER_COMPOSE down"
    echo ""
else
    echo "To build and run with Docker:"
    echo "  docker build -t plavka-bot ."
    echo "  docker run -d --name plavka-bot --env-file .env -v \$(pwd)/Контроль:/app/Контроль plavka-bot"
    echo ""
fi
