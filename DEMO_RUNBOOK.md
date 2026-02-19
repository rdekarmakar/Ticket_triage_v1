# Ticket Triage System - Demo Runbook

This guide walks through common demo scenarios to showcase the system's capabilities.

## Prerequisites

1. Server is running:
   ```bash
   python -m cli.main serve --port 8080
   ```

2. Runbooks are indexed:
   ```bash
   python -m cli.main index
   ```

---

## Server Management

### Start the Server

```bash
# Start on default port 8080
python -m cli.main serve --port 8080

# Start with auto-reload (for development)
python -m cli.main serve --port 8080 --reload

# Start on a different port
python -m cli.main serve --port 9000
```

### Stop the Server

**Method 1: Ctrl + C (Recommended)**

Press `Ctrl + C` in the terminal where the server is running.

```
^C
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [12345]
```

**Method 2: Kill by Port (Windows)**

```cmd
# Find process using port 8080
netstat -ano | findstr :8080

# Kill by PID (replace 12345 with actual PID from above)
taskkill /PID 12345 /F
```

**Method 3: Kill by Port (Windows PowerShell)**

```powershell
# Find and kill in one command
Get-NetTCPConnection -LocalPort 8080 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
```

**Method 4: Kill by Port (Linux/Mac)**

```bash
# Find process using port 8080
lsof -i :8080

# Kill by port directly
kill $(lsof -t -i:8080)

# Force kill if needed
kill -9 $(lsof -t -i:8080)
```

**Method 5: Kill all Python processes (Use with caution)**

```cmd
# Windows - kills ALL python processes
taskkill /IM python.exe /F

# Linux/Mac
pkill -f python
```

### Restart the Server

1. Stop the server: `Ctrl + C`
2. Start again:
   ```bash
   python -m cli.main serve --port 8080
   ```

### Check if Server is Running

```bash
# Using curl
curl http://localhost:8080/health

# Using browser
# Open http://localhost:8080/health
```

Expected response:
```json
{"status": "healthy", "version": "1.0.0"}
```

### Running Server in Background (Windows)

```bash
# Start in background
start /B python -m cli.main serve --port 8080 > server.log 2>&1

# View logs
type server.log

# Find and stop the process
tasklist | findstr python
taskkill /PID <process_id> /F
```

### Running Server in Background (Linux/Mac)

```bash
# Start in background
nohup python -m cli.main serve --port 8080 > server.log 2>&1 &

# View logs
tail -f server.log

# Find and stop the process
ps aux | grep "cli.main serve"
kill <process_id>
```

---

## Demo 1: CLI - Search Runbooks

Search for relevant runbook content without creating a ticket.

```bash
# Search for CPU-related issues
python -m cli.main query "high CPU usage on production server"

# Search for database issues
python -m cli.main query "database connection pool exhausted"

# Search for disk space issues
python -m cli.main query "server disk full alert"
```

**Expected Output:** Relevant runbook sections with similarity scores.

---

## Demo 2: CLI - Generate Triage Suggestion & Create Ticket

Create a ticket with AI-powered triage suggestions.

```bash
# Infrastructure alert - High CPU (creates ticket)
python -m cli.main suggest "CRITICAL: CPU usage at 98% on web-server-01 for 15 minutes"

# Application alert - API timeout (creates ticket)
python -m cli.main suggest "ALERT: API Gateway returning 504 timeout errors. Latency spiked to 30s. Affecting 40% of requests to /api/v2/orders endpoint"

# Database alert - Connection issues (creates ticket)
python -m cli.main suggest "ERROR: PostgreSQL connection pool exhausted on db-primary-01. Active connections: 100/100. Waiting queries: 47"

# Memory alert (creates ticket)
python -m cli.main suggest "WARNING: Memory usage at 92% on app-server-03. OOM killer may trigger soon"

# Disk alert (creates ticket)
python -m cli.main suggest "CRITICAL: Disk usage at 95% on /var/log partition. Server: log-aggregator-01"

# Quick triage WITHOUT creating a ticket (use --no-ticket or -n flag)
python -m cli.main suggest "CRITICAL: Test alert" --no-ticket
python -m cli.main suggest "CRITICAL: Test alert" -n
```

**Expected Output:**
- Ticket ID and details
- AI-generated triage suggestion with:
  - Summary
  - Immediate Actions
  - Root Cause Hypothesis
  - Escalation Recommendation
  - Confidence Level
- Links to view ticket in CLI and Dashboard

---

## Demo 3: CLI - View Tickets

```bash
# List all tickets
python -m cli.main tickets

# Filter by status
python -m cli.main tickets --status open

# Filter by severity
python -m cli.main tickets --severity critical

# Combine filters
python -m cli.main tickets --status open --severity high

# View specific ticket details
python -m cli.main show 1

# View ticket statistics
python -m cli.main stats
```

---

## Demo 4: REST API - Using Swagger UI

Open http://localhost:8080/docs in your browser.

### 4.1 Create Ticket (without triage)

**Endpoint:** `POST /api/tickets`

```json
{
  "title": "Redis cluster node failure",
  "description": "Redis node redis-03 is not responding to health checks",
  "raw_message": "CRITICAL: Redis cluster node redis-03 unreachable. Cluster health degraded. Replication lag increasing.",
  "severity": "critical",
  "alert_type": "infrastructure"
}
```

### 4.2 Run Triage on Ticket

**Endpoint:** `POST /api/tickets/{ticket_id}/triage`

Enter the ticket ID from step 4.1.

### 4.3 List Tickets with Filters

**Endpoint:** `GET /api/tickets`

Parameters:
- `status`: open
- `severity`: critical
- `limit`: 10

### 4.4 Get Ticket Statistics

**Endpoint:** `GET /api/tickets/stats`

### 4.5 Update Ticket Status

**Endpoint:** `PATCH /api/tickets/{ticket_id}`

```json
{
  "status": "in_progress"
}
```

---

## Demo 5: REST API - Using cURL

```bash
# Create a ticket
curl -X POST http://localhost:8080/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Kubernetes pod crash loop",
    "description": "Payment service pods are in CrashLoopBackOff state",
    "raw_message": "ALERT: payment-service-7d4f9b8c6-x2k9m CrashLoopBackOff. Restart count: 15. Last error: OOMKilled",
    "severity": "critical",
    "alert_type": "application"
  }'

# Run triage (replace 5 with actual ticket ID)
curl -X POST http://localhost:8080/api/tickets/5/triage

# Get ticket details
curl http://localhost:8080/api/tickets/5

# List all open tickets
curl "http://localhost:8080/api/tickets?status=open"

# Get statistics
curl http://localhost:8080/api/tickets/stats
```

---

## Demo 6: Web Dashboard

### 6.1 Access Dashboard

1. Open http://localhost:8080/dashboard
2. Login with credentials:
   - Username: `admin`
   - Password: `changeme`

### 6.2 Dashboard Features

- **Overview**: See ticket counts by severity and status
- **Recent Tickets**: Click any ticket to view details
- **All Tickets**: View filterable list of all tickets
- **Ticket Detail**:
  - View AI triage suggestion
  - See runbook references
  - Change ticket status
  - Re-run triage if needed

---

## Demo 7: Sample Alert Scenarios

Use these realistic alerts to demonstrate the system:

### Infrastructure Alerts

```bash
# CPU spike
python -m cli.main suggest "CRITICAL: CPU utilization at 99% on prod-api-01. Load average: 45.2, 42.1, 38.7. Top process: java (pid 12345)"

# Memory exhaustion
python -m cli.main suggest "ALERT: Out of memory condition on worker-node-05. Available: 128MB of 32GB. OOM score adjustment triggered"

# Disk full
python -m cli.main suggest "CRITICAL: /data partition at 98% on database-primary. Growth rate: 2GB/hour. Estimated full in 4 hours"

# Network issues
python -m cli.main suggest "WARNING: High packet loss (15%) detected between us-east-1a and us-east-1b. Latency increased from 1ms to 45ms"
```

### Application Alerts

```bash
# HTTP 500 errors
python -m cli.main suggest "ALERT: HTTP 500 error rate spiked to 25% on /api/checkout endpoint. Affected users: ~5000 in last 5 minutes"

# Slow response times
python -m cli.main suggest "WARNING: P99 latency for user-service exceeded 5s threshold. Current P99: 8.2s, P50: 1.2s"

# Queue backlog
python -m cli.main suggest "CRITICAL: RabbitMQ queue 'order-processing' has 50,000 pending messages. Consumer count: 0. Last ack: 30 minutes ago"

# Database connection errors
python -m cli.main suggest "ERROR: Unable to establish connection to MySQL primary. Error: Too many connections. Current: 500/500"
```

### Monitoring Alerts

```bash
# Service down
python -m cli.main suggest "CRITICAL: Health check failed for payment-gateway service. Last successful check: 5 minutes ago. Consecutive failures: 10"

# SSL certificate expiring
python -m cli.main suggest "WARNING: SSL certificate for api.example.com expires in 7 days. Serial: ABC123. Issuer: Let's Encrypt"

# Backup failure
python -m cli.main suggest "ALERT: Daily backup job failed for production database. Error: Insufficient disk space on backup server. Last successful backup: 2 days ago"
```

---

## Demo 8: End-to-End Flow

Complete demonstration showing the full triage workflow:

```bash
# 1. Check system health
curl http://localhost:8080/health

# 2. View current statistics
python -m cli.main stats

# 3. Simulate an incoming alert and create triaged ticket
python -m cli.main suggest "CRITICAL: Multiple services reporting database connection timeouts. Affected: user-service, order-service, inventory-service. Connection pool exhausted on db-primary-01"

# 4. List tickets to see the new one
python -m cli.main tickets --status open

# 5. View the ticket details (use actual ID)
python -m cli.main show 1

# 6. Open dashboard to see visual representation
# http://localhost:8080/dashboard

# 7. Update ticket status via API
curl -X PATCH http://localhost:8080/api/tickets/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# 8. Check updated statistics
python -m cli.main stats
```

---

## Quick Reference

| Action | Command/URL |
|--------|-------------|
| Start server | `python -m cli.main serve --port 8080` |
| Index runbooks | `python -m cli.main index` |
| Search runbooks | `python -m cli.main query "search term"` |
| Create triaged ticket | `python -m cli.main suggest "alert message"` |
| Triage without ticket | `python -m cli.main suggest "alert" --no-ticket` |
| List tickets | `python -m cli.main tickets` |
| View ticket | `python -m cli.main show {id}` |
| Statistics | `python -m cli.main stats` |
| Dashboard | http://localhost:8080/dashboard |
| API Docs | http://localhost:8080/docs |
| Health Check | http://localhost:8080/health |

---

## Troubleshooting Demo Issues

**"No relevant runbook sections found"**
```bash
python -m cli.main index --force
```

**"LLM API error"**
- Check GROQ_API_KEY in .env file
- Verify API quota at console.groq.com

**"Connection refused"**
```bash
python -m cli.main serve --port 8080
```

**Dashboard shows 401 Unauthorized**
- Use credentials: admin / changeme
- Or check DASHBOARD_USERNAME/PASSWORD in .env
