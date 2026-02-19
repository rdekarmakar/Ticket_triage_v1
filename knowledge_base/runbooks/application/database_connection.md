# Database Connection Issues Runbook

## Overview
This runbook covers procedures for handling database connectivity problems including connection timeouts, pool exhaustion, and authentication failures.

## Alert Patterns
- "Database connection failed"
- "Connection pool exhausted"
- "Connection timeout"
- "Too many connections"
- "Database unreachable"
- "Authentication failed"

## Severity Classification
- **Critical**: Complete database unavailability
- **High**: Connection pool exhaustion or >50% connection failures
- **Medium**: Intermittent connection issues

## Immediate Actions

### Step 1: Verify Database Status
```bash
# Check database server is reachable
ping database-host
nc -zv database-host 5432

# Check database process
systemctl status postgresql  # or mysql, etc.

# Check database logs
tail -100 /var/log/postgresql/postgresql-14-main.log
```

### Step 2: Check Connection State

#### For PostgreSQL
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Connection by state
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;

-- Idle connections
SELECT pid, usename, application_name, state, query_start
FROM pg_stat_activity WHERE state = 'idle';

-- Blocked queries
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid
FROM pg_locks blocked_locks
JOIN pg_locks blocking_locks ON blocked_locks.locktype = blocking_locks.locktype;
```

#### For MySQL
```sql
-- Show all connections
SHOW PROCESSLIST;

-- Connection count
SHOW STATUS LIKE 'Threads_connected';

-- Max connections setting
SHOW VARIABLES LIKE 'max_connections';
```

### Step 3: Application-Side Checks
```bash
# Check application connection pool settings
grep -r "pool\|connection" /etc/application/config.yml

# Check for connection leaks in logs
grep -i "connection\|pool\|leak" /var/log/application/*.log | tail -50
```

### Step 4: Mitigation

#### If Connection Pool Exhausted
```bash
# Kill idle connections (PostgreSQL)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' AND query_start < now() - interval '10 minutes';
```

#### If Too Many Connections
1. Increase max_connections (temporary)
2. Restart application to reset connection pool
3. Scale down application instances temporarily

#### If Database Unreachable
1. Check network connectivity
2. Check firewall rules
3. Verify database server is running
4. Check disk space on database server

### Step 5: Verify Resolution
```bash
# Test connection from application server
psql -h database-host -U app_user -d app_database -c "SELECT 1;"

# Monitor connection count
watch -n 5 'psql -c "SELECT count(*) FROM pg_stat_activity;"'
```

## Root Cause Analysis
- Check for connection leak in application code
- Review connection pool configuration
- Analyze query performance
- Check for network issues
- Review recent changes

## Escalation Criteria
- Escalate to Database Team if:
  - Database server issues
  - Performance degradation
  - Need configuration changes
- Escalate to Network Team if:
  - Network connectivity issues
  - Firewall/security group changes needed
- Escalate to Development Team if:
  - Connection leak identified
  - Application code issue

## Prevention
- Implement connection pooling properly
- Set connection timeouts
- Monitor connection counts
- Regular connection pool health checks
- Implement retry logic with backoff
