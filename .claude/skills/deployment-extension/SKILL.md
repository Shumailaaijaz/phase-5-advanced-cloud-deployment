---
name: deployment-extension
description: Extend Phase II deployment for Phase III chatbot and MCP services with proper isolation, secrets management, and CI/CD updates. Use when deploying the AI chatbot infrastructure.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Deployment Extension Skill

## Purpose

Extend the Phase II deployment configuration to support Phase III services including the MCP server, agent runner, and chatbot infrastructure with proper service isolation, secrets management, and CI/CD integration.

## Used by

- frontend-integrator agent
- security-auditor agent
- integration-flow-tester agent

## When to Use

- Adding MCP server to deployment
- Configuring agent runner service
- Updating CI/CD pipelines for chatbot testing
- Managing API keys and secrets
- Setting up horizontal scaling

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phase2_config` | object | Yes | Existing deployment files |
| `new_services` | list | Yes | Services to add (mcp_server, agent_runner) |
| `env_vars` | dict | Yes | Additional environment variables |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `updated_config` | YAML | Modified docker-compose, CI/CD |
| `env_templates` | text | .env.example files |
| `deployment_script` | shell | Extended deployment script |

## Docker Compose Configuration

### Full docker-compose.yml

```yaml
# File: docker-compose.yml
# [Skill]: Deployment Extension

version: '3.8'

services:
  # ===================
  # Phase II Services
  # ===================

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_MCP_URL=http://mcp:8001
    depends_on:
      - backend
      - mcp
    restart: unless-stopped
    networks:
      - app-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET}
      - ENV=${ENV:-production}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=${DB_USER:-postgres}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME:-todoapp}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ===================
  # Phase III Services
  # ===================

  mcp:
    build:
      context: ./mcp
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET}
      - MCP_API_KEY=${MCP_API_KEY}
      - ENV=${ENV:-production}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3

  agent:
    build:
      context: ./agent
      dockerfile: Dockerfile
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MCP_SERVER_URL=http://mcp:8001
      - DATABASE_URL=${DATABASE_URL}
      - BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET}
      - ENV=${ENV:-production}
    depends_on:
      mcp:
        condition: service_healthy
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - app-network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  # ===================
  # Infrastructure
  # ===================

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on:
      - frontend
      - backend
      - mcp
    restart: unless-stopped
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

### MCP Service Dockerfile

```dockerfile
# File: mcp/Dockerfile
# [Skill]: Deployment Extension

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8001/health/ready || exit 1

# Run server
CMD ["uvicorn", "mcp.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Agent Service Dockerfile

```dockerfile
# File: agent/Dockerfile
# [Skill]: Deployment Extension

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# No exposed port - internal service only

# Run agent service
CMD ["python", "-m", "agent.main"]
```

## Environment Templates

### .env.example

```bash
# File: .env.example
# [Skill]: Deployment Extension

# ===================
# Phase II Variables
# ===================

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Local DB (for development)
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_NAME=todoapp

# Authentication
BETTER_AUTH_SECRET=your-32-character-secret-key-here

# Environment
ENV=development

# ===================
# Phase III Variables
# ===================

# OpenAI API (REQUIRED for chatbot)
OPENAI_API_KEY=sk-your-openai-api-key

# OpenAI Model
OPENAI_MODEL=gpt-4-turbo-preview

# MCP Server
MCP_API_KEY=your-mcp-api-key-for-server-to-server
MCP_HOST=0.0.0.0
MCP_PORT=8001

# Agent Configuration
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=30

# Rate Limiting
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW_SECONDS=60

# Redis (for caching/sessions)
REDIS_URL=redis://localhost:6379/0
```

### .env.production.example

```bash
# File: .env.production.example
# [Skill]: Deployment Extension

# ===================
# Production Settings
# ===================

# Database (Neon PostgreSQL - production)
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require

# Authentication (use strong secret)
BETTER_AUTH_SECRET=generate-with-openssl-rand-base64-32

# Environment
ENV=production

# OpenAI API
OPENAI_API_KEY=sk-your-production-openai-key
OPENAI_MODEL=gpt-4-turbo-preview

# MCP Server
MCP_API_KEY=generate-unique-api-key

# Rate Limiting (stricter for production)
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60

# Redis
REDIS_URL=redis://redis:6379/0

# Logging
LOG_LEVEL=WARNING
```

## CI/CD Configuration

### GitHub Actions Workflow

```yaml
# File: .github/workflows/deploy.yml
# [Skill]: Deployment Extension

name: Deploy Phase III

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository }}

jobs:
  # ===================
  # Test Phase
  # ===================

  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
          BETTER_AUTH_SECRET: test-secret-key-12345
        run: |
          cd backend
          pytest tests/ -v

  test-mcp:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd mcp
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx

      - name: Run MCP tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
          BETTER_AUTH_SECRET: test-secret-key-12345
          MCP_API_KEY: test-api-key
        run: |
          cd mcp
          pytest tests/ -v

  test-chatbot-integration:
    runs-on: ubuntu-latest
    needs: [test-backend, test-mcp]
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install all dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -r mcp/requirements.txt
          pip install -r agent/requirements.txt
          pip install pytest pytest-asyncio httpx

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
          BETTER_AUTH_SECRET: test-secret-key-12345
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          pytest tests/integration/ -v --tb=short

  # ===================
  # Build Phase
  # ===================

  build:
    runs-on: ubuntu-latest
    needs: [test-chatbot-integration]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    strategy:
      matrix:
        service: [frontend, backend, mcp, agent]

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push ${{ matrix.service }}
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:${{ github.sha }}

  # ===================
  # Deploy Phase
  # ===================

  deploy:
    runs-on: ubuntu-latest
    needs: build
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        env:
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
        run: |
          echo "$DEPLOY_KEY" > deploy_key
          chmod 600 deploy_key
          ssh -i deploy_key -o StrictHostKeyChecking=no $DEPLOY_HOST << 'EOF'
            cd /app
            docker compose pull
            docker compose up -d --remove-orphans
            docker system prune -f
          EOF
```

## Deployment Script

```bash
#!/bin/bash
# File: scripts/deploy.sh
# [Skill]: Deployment Extension

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Phase III Deployment ===${NC}"

# Check required env vars
required_vars=("DATABASE_URL" "BETTER_AUTH_SECRET" "OPENAI_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: $var is not set${NC}"
        exit 1
    fi
done

echo -e "${YELLOW}Checking services...${NC}"

# Pull latest images
echo -e "${YELLOW}Pulling latest images...${NC}"
docker compose pull

# Run database migrations
echo -e "${YELLOW}Running migrations...${NC}"
docker compose run --rm backend alembic upgrade head
docker compose run --rm mcp alembic upgrade head

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker compose up -d

# Wait for health checks
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check health
services=("backend" "mcp" "frontend")
for service in "${services[@]}"; do
    if docker compose ps "$service" | grep -q "healthy"; then
        echo -e "${GREEN}✓ $service is healthy${NC}"
    else
        echo -e "${RED}✗ $service is not healthy${NC}"
        docker compose logs "$service" --tail=50
    fi
done

# Cleanup
echo -e "${YELLOW}Cleaning up...${NC}"
docker system prune -f

echo -e "${GREEN}=== Deployment Complete ===${NC}"
```

## Nginx Configuration

```nginx
# File: nginx/nginx.conf
# [Skill]: Deployment Extension

upstream frontend {
    server frontend:3000;
}

upstream backend {
    server backend:8000;
}

upstream mcp {
    server mcp:8001;
}

server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # MCP Server
    location /mcp/ {
        proxy_pass http://mcp/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Health checks (no auth)
    location /health {
        proxy_pass http://backend/health;
    }
}
```

## Quality Standards

### Service Isolation
- Separate containers for MCP and agent
- Internal network communication
- No direct external access to agent service

### Resilience
- Health checks on all services
- Automatic restart policies
- Database state persistence via volumes

### Secrets Management
- All API keys in environment variables
- No secrets in Docker images
- Separate .env files per environment

### CI/CD
- Unit tests for each service
- Integration tests for chatbot flow
- Automated deployment on main branch

### Horizontal Scaling
- Stateless services (MCP, agent)
- Load balancer ready (nginx)
- Redis for shared state if needed

## Verification Checklist

- [ ] All services defined in docker-compose.yml
- [ ] Health checks configured for each service
- [ ] Environment variables documented in .env.example
- [ ] CI/CD pipeline includes chatbot tests
- [ ] Secrets not committed to repository
- [ ] Nginx configured for routing
- [ ] Database migrations run before service start
- [ ] Deployment script validates required vars

## Output Format

1. **docker-compose.yml** - Full service configuration
2. **Dockerfiles** - For mcp/ and agent/
3. **.env.example** - Environment template
4. **.github/workflows/deploy.yml** - CI/CD pipeline
5. **scripts/deploy.sh** - Deployment script
6. **nginx/nginx.conf** - Load balancer config
