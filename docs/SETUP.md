# Setup Guide

Complete setup instructions for the PDF Text Extraction Engine.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

1. **Node.js** (>= 18.0.0)
   ```bash
   # Check version
   node --version
   
   # Install from https://nodejs.org/
   # Or use nvm:
   nvm install 18
   nvm use 18
   ```

2. **npm** (>= 9.0.0)
   ```bash
   # Check version
   npm --version
   
   # Update if needed
   npm install -g npm@latest
   ```

3. **PostgreSQL** (>= 12)
   ```bash
   # Check version
   psql --version
   
   # Install on Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # Install on macOS
   brew install postgresql
   
   # Install on Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

### Optional Tools

- **pgAdmin**: PostgreSQL GUI client
- **Postman/Insomnia**: API testing
- **Docker**: For containerized deployment

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd pdf-extraction-engine
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required dependencies:
- **Runtime**: express, pdf-parse, pg, multer, date-fns, chrono-node, dotenv
- **Development**: TypeScript, Jest, ESLint, Prettier, nodemon

### 3. Verify Installation

```bash
# Check that dependencies installed correctly
npm list --depth=0

# Verify TypeScript compilation works
npm run build
```

## Database Setup

### 1. Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Or on Windows/macOS
psql -U postgres
```

```sql
-- Create database
CREATE DATABASE pdfextractor;

-- Create user (optional, for security)
CREATE USER pdfuser WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pdfextractor TO pdfuser;

-- Exit
\q
```

### 2. Verify Database Connection

```bash
# Test connection
psql -h localhost -U postgres -d pdfextractor -c "SELECT version();"
```

### 3. Run Migrations

The migration script will create all required tables and indexes:

```bash
npm run migrate
```

This creates:
- `documents` table with indexes
- `extraction_results` table with JSONB indexes
- Trigger functions for automatic timestamp updates

### 4. Verify Tables Created

```bash
psql -h localhost -U postgres -d pdfextractor
```

```sql
-- List tables
\dt

-- Describe documents table
\d documents

-- Describe extraction_results table
\d extraction_results

-- Exit
\q
```

## Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your settings:

```bash
# Application Configuration
NODE_ENV=development          # Environment: development | production | test
PORT=3000                     # Server port
LOG_LEVEL=info               # Logging level: debug | info | warn | error

# Database Configuration
DB_HOST=localhost            # Database host
DB_PORT=5432                # Database port
DB_USER=postgres            # Database username
DB_PASSWORD=postgres        # Database password (change in production!)
DB_NAME=pdfextractor        # Database name

# Database Pool Configuration
DB_POOL_MIN=2               # Minimum connections in pool
DB_POOL_MAX=10              # Maximum connections in pool

# File Upload Configuration
MAX_FILE_SIZE=10485760      # Max file size in bytes (10MB)
UPLOAD_DIR=./uploads        # Upload directory path

# API Configuration
API_PREFIX=/api             # API route prefix
CORS_ORIGIN=http://localhost:3000  # CORS allowed origin
```

### 3. Create Upload Directory

```bash
mkdir -p uploads
chmod 755 uploads
```

### 4. Validate Configuration

The application will validate configuration on startup. Test it:

```bash
npm run dev
```

Look for output like:
```
[INFO] Starting PDF Extraction Engine
[INFO] Database connection established
[INFO] Server listening on port 3000
```

## Running the Application

### Development Mode

Start with auto-reload on file changes:

```bash
npm run dev
```

The server will:
- Start on the port specified in `.env`
- Auto-restart when you modify source files
- Use ts-node to run TypeScript directly

### Production Mode

Build and run the compiled JavaScript:

```bash
# Build TypeScript to JavaScript
npm run build

# Start production server
npm start
```

### Verify Server is Running

```bash
# Test health endpoint (if implemented)
curl http://localhost:3000/health

# Test document listing
curl http://localhost:3000/api/documents
```

## Development Setup

### 1. Editor Configuration

**VS Code** (recommended):

Install extensions:
- ESLint
- Prettier
- TypeScript
- PostgreSQL

Settings (`.vscode/settings.json`):
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

### 2. Git Hooks (Optional)

Install husky for pre-commit hooks:

```bash
npm install --save-dev husky lint-staged
npx husky install

# Add pre-commit hook
npx husky add .husky/pre-commit "npm run lint && npm run format:check"
```

### 3. Running Tests

```bash
# All tests
npm test

# Watch mode (auto-rerun on changes)
npm run test:watch

# Integration tests only
npm run test:integration

# E2E tests only
npm run test:e2e

# Coverage report
npm run test:coverage
```

### 4. Code Quality Checks

```bash
# Lint code
npm run lint

# Fix linting issues automatically
npm run lint:fix

# Format code
npm run format

# Check formatting
npm run format:check
```

## Production Deployment

### 1. Environment Setup

Create production `.env`:

```bash
NODE_ENV=production
PORT=3000
LOG_LEVEL=warn

# Use secure credentials
DB_HOST=<production-db-host>
DB_PORT=5432
DB_USER=<production-user>
DB_PASSWORD=<strong-password>
DB_NAME=pdfextractor

# Increase pool size for production
DB_POOL_MIN=5
DB_POOL_MAX=20

# Configure production storage
UPLOAD_DIR=/var/app/uploads

# Configure CORS for your domain
CORS_ORIGIN=https://yourdomain.com
```

### 2. Build Application

```bash
npm run build
```

This creates optimized JavaScript in `dist/` directory.

### 3. Database Migration

Run migrations on production database:

```bash
npm run migrate
```

### 4. Process Manager

Use PM2 to manage the Node.js process:

```bash
# Install PM2 globally
npm install -g pm2

# Start application
pm2 start dist/index.js --name pdf-extraction-engine

# Configure auto-restart on reboot
pm2 startup
pm2 save

# Monitor application
pm2 monit

# View logs
pm2 logs pdf-extraction-engine

# Restart after updates
pm2 restart pdf-extraction-engine
```

### 5. Reverse Proxy (Nginx)

Configure Nginx as reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Increase upload size for PDFs
    client_max_body_size 10M;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 6. Docker Deployment (Optional)

Create `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DB_HOST=db
      - DB_PORT=5432
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - DB_NAME=pdfextractor
    depends_on:
      - db
    volumes:
      - ./uploads:/app/uploads

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=pdfextractor
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres-data:
```

Deploy:

```bash
docker-compose up -d
```

## Troubleshooting

### Database Connection Issues

**Error**: `ECONNREFUSED` or `Connection refused`

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Check PostgreSQL is listening
netstat -an | grep 5432
```

**Error**: `password authentication failed`

- Verify credentials in `.env` match database
- Check PostgreSQL `pg_hba.conf` allows password authentication
- Reset password if needed:

```sql
ALTER USER postgres WITH PASSWORD 'newpassword';
```

### Migration Fails

**Error**: `relation already exists`

Tables already exist. Either:
1. Drop and recreate database (loses data)
2. Manually run migration SQL files

```bash
# Drop database (WARNING: destroys all data)
psql -U postgres -c "DROP DATABASE pdfextractor;"
psql -U postgres -c "CREATE DATABASE pdfextractor;"

# Re-run migrations
npm run migrate
```

### Upload Directory Errors

**Error**: `ENOENT: no such file or directory`

```bash
# Create upload directory
mkdir -p uploads

# Set permissions
chmod 755 uploads

# Verify in .env
echo $UPLOAD_DIR
```

### Port Already in Use

**Error**: `EADDRINUSE: address already in use`

```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>

# Or use different port in .env
PORT=3001
```

### TypeScript Compilation Errors

```bash
# Clean build artifacts
rm -rf dist/

# Reinstall dependencies
rm -rf node_modules/
npm install

# Rebuild
npm run build
```

### PDF Extraction Fails

**Issue**: No text extracted from PDF

- Verify PDF contains text (not scanned image):
  ```bash
  pdftotext certificate.pdf -
  ```
- If scanned, OCR is required (not currently supported)

### Low Confidence Scores

**Issue**: Extracted metadata has low confidence

- Review PDF format matches expected certificate structure
- Check if document is in Romanian
- Examine extracted text in database to verify parsing patterns

### Database Performance Issues

**Issue**: Slow queries

```sql
-- Check indexes exist
SELECT * FROM pg_indexes WHERE tablename IN ('documents', 'extraction_results');

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM documents WHERE processing_status = 'completed';

-- Rebuild indexes if needed
REINDEX TABLE documents;
REINDEX TABLE extraction_results;
```

## Security Checklist

Before production deployment:

- [ ] Change default database password
- [ ] Use environment-specific `.env` files
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS appropriately
- [ ] Set up firewall rules
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Enable PostgreSQL SSL connections
- [ ] Regular security updates
- [ ] Set up monitoring and alerting

## Next Steps

After setup is complete:

1. Review [API Documentation](./API.md) for usage examples
2. Test with sample PDF certificates (see `tests/fixtures/`)
3. Configure monitoring and logging
4. Set up backup strategy for database
5. Implement authentication if needed
6. Configure CI/CD pipeline

## Support

For issues:
- Check application logs: `pm2 logs` or `npm run dev` output
- Review PostgreSQL logs: `/var/log/postgresql/`
- Enable debug logging: `LOG_LEVEL=debug` in `.env`
- Check database connection: `npm run migrate`
