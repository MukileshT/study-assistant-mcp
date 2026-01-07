# Deployment Guide

Guide for deploying Study Assistant MCP in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Production Setup](#production-setup)
3. [Docker Deployment](#docker-deployment)
4. [Environment Variables](#environment-variables)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Backup & Recovery](#backup--recovery)

---

## Local Development

### Setup

```bash
# Clone repository
git clone <repository-url>
cd study-assistant-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Validate setup
python scripts/validate_setup.py

# Run tests
./scripts/run_tests.sh fast
```

### Development Workflow

```bash
# Activate environment
source venv/bin/activate

# Run in development mode
export APP_ENV=development
export LOG_LEVEL=DEBUG

# Process test note
python -m src.main process test_note.jpg

# Run specific tests
pytest tests/test_processors.py -v

# Check code quality
black src/ --check
flake8 src/
```

---

## Production Setup

### System Requirements

**Minimum:**
- Python 3.11+
- 2GB RAM
- 10GB disk space
- Internet connection

**Recommended:**
- Python 3.11+
- 4GB RAM
- 50GB disk space
- Fast internet

### Production Installation

```bash
# System dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3-pip \
    python3-venv \
    git

# Clone and setup
git clone <repository-url> /opt/study-assistant
cd /opt/study-assistant

# Create production environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Production configuration
cp .env.example .env
nano .env  # Set production values

# Set environment
export APP_ENV=production
export LOG_LEVEL=INFO

# Create data directories
mkdir -p data/{cache,uploads,processed,logs}

# Set permissions
chmod 755 data
chmod 644 .env

# Initialize database
python -c "import asyncio; from src.storage import DatabaseManager; asyncio.run(DatabaseManager().initialize())"

# Validate
python scripts/validate_setup.py
```

### Security Hardening

```bash
# Restrict file permissions
chmod 600 .env
chmod 700 data/

# Create dedicated user
sudo useradd -r -s /bin/false studyassistant

# Change ownership
sudo chown -R studyassistant:studyassistant /opt/study-assistant

# Run as service user
sudo -u studyassistant python -m src.main process note.jpg
```

---

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/{cache,uploads,processed,logs}

# Environment
ENV APP_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.core import StudyAssistantAgent; import asyncio; asyncio.run(StudyAssistantAgent().initialize())" || exit 1

# Run
CMD ["python", "-m", "src.main", "test"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  study-assistant:
    build: .
    container_name: study-assistant
    environment:
      - APP_ENV=production
      - LOG_LEVEL=INFO
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
    networks:
      - study-network

networks:
  study-network:
    driver: bridge
```

### Build and Run

```bash
# Build image
docker build -t study-assistant:latest .

# Run with compose
docker-compose up -d

# View logs
docker-compose logs -f

# Process note
docker-compose exec study-assistant python -m src.main process /data/note.jpg

# Stop
docker-compose down
```

---

## Environment Variables

### Required Variables

```bash
# API Keys
GOOGLE_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
NOTION_API_KEY=your_notion_token
NOTION_DATABASE_ID=your_database_id

# Optional
NOTION_PLANS_DATABASE_ID=your_plans_db_id
```

### Configuration Variables

```bash
# Application
APP_ENV=production
LOG_LEVEL=INFO
DATA_DIR=./data
MAX_IMAGE_SIZE_MB=10

# Models
VISION_MODEL=gemini-1.5-flash
TEXT_MODEL=llama-3.1-70b-versatile
PLANNING_MODEL=gemini-1.5-pro

# Rate Limits
GEMINI_RPM_LIMIT=15
GROQ_RPM_LIMIT=30

# Features
ENABLE_CACHING=true
AUTO_GENERATE_PLANS=true
PLAN_GENERATION_TIME=20:00

# User Preferences
LEARNING_STYLE=visual
NOTE_DETAIL_LEVEL=standard
TIMEZONE=America/New_York
```

---

## Monitoring & Maintenance

### Logging

Logs are stored in `data/logs/`:

```bash
# View logs
tail -f data/logs/study_assistant_*.log

# Monitor errors
grep ERROR data/logs/*.log

# Check API usage
python -m src.main stats
```

### Health Checks

```bash
# System validation
python scripts/validate_setup.py

# API tests
python -m src.main test

# Database check
python -c "import asyncio; from src.storage import DatabaseManager; asyncio.run(DatabaseManager().initialize())"
```

### Performance Monitoring

```python
# In application
from src.utils.performance import get_performance_monitor

monitor = get_performance_monitor()
summary = monitor.get_summary()
print(summary)
```

### Scheduled Maintenance

```bash
# Crontab example
# Clean up old files weekly
0 2 * * 0 cd /opt/study-assistant && python -m src.main cleanup --days 30

# Generate daily plan
0 20 * * * cd /opt/study-assistant && python -m src.main plan

# Health check
*/30 * * * * cd /opt/study-assistant && python -m src.main test || echo "Health check failed"
```

---

## Backup & Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/study-assistant"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
mkdir -p "$BACKUP_DIR/$DATE"

# Backup database
cp data/local.db "$BACKUP_DIR/$DATE/"

# Backup configuration
cp .env "$BACKUP_DIR/$DATE/"
cp -r config "$BACKUP_DIR/$DATE/"

# Backup processed notes metadata
tar -czf "$BACKUP_DIR/$DATE/processed.tar.gz" data/processed/

# Keep last 7 days
find "$BACKUP_DIR" -type d -mtime +7 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
```

### Restore Procedure

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: ./restore.sh /path/to/backup"
    exit 1
fi

# Stop service
docker-compose down  # If using Docker

# Restore database
cp "$BACKUP_DIR/local.db" data/

# Restore configuration
cp "$BACKUP_DIR/.env" .
cp -r "$BACKUP_DIR/config" .

# Restore processed files
tar -xzf "$BACKUP_DIR/processed.tar.gz" -C data/

# Start service
docker-compose up -d

echo "Restore completed"
```

### Disaster Recovery

1. **Database Corruption**
   ```bash
   # Restore from backup
   cp backup/latest/local.db data/
   
   # Reinitialize if needed
   python -c "import asyncio; from src.storage import DatabaseManager; asyncio.run(DatabaseManager().initialize())"
   ```

2. **API Key Compromise**
   ```bash
   # Regenerate keys at providers
   # Update .env
   nano .env
   
   # Restart application
   docker-compose restart
   ```

3. **Data Loss**
   ```bash
   # Restore from Notion (notes are safe there)
   # Local data can be recreated
   
   # Reprocess if needed
   python -m src.main process historical/*.jpg
   ```

---

## Scaling Considerations

### Horizontal Scaling

Currently single-instance design. For multiple instances:

1. **Shared Database**
   - Use PostgreSQL instead of SQLite
   - Configure connection pooling

2. **Distributed Caching**
   - Use Redis for shared cache
   - Configure cache invalidation

3. **Load Balancing**
   - API rate limiting across instances
   - Queue-based processing

### Vertical Scaling

Optimize single instance:

```python
# In .env
MAX_CONCURRENT_PROCESSING=5
ENABLE_BATCH_PROCESSING=true
CACHE_SIZE_MB=500
```

---

## Troubleshooting Production Issues

### High Memory Usage

```bash
# Monitor memory
docker stats study-assistant

# Reduce concurrent operations
# In code, limit semaphore
```

### API Rate Limits

```bash
# Spread processing
python -m src.main process *.jpg --delay 2

# Use batch processing
```

### Disk Space

```bash
# Check usage
du -sh data/*

# Clean up
python -m src.main cleanup --days 7

# Compress old logs
gzip data/logs/*.log
```

---

## Production Checklist

Before going live:

- [ ] All API keys configured
- [ ] Notion workspace set up
- [ ] Database initialized
- [ ] Backup system configured
- [ ] Monitoring in place
- [ ] Log rotation configured
- [ ] SSL/TLS if exposing APIs
- [ ] Rate limiting configured
- [ ] Error alerting set up
- [ ] Documentation updated
- [ ] Team training completed

---

**Production-Ready! 🚀**