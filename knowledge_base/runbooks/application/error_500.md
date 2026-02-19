# HTTP 500 Internal Server Error Runbook

## Overview
This runbook covers procedures for handling HTTP 500 Internal Server Error alerts in production applications.

## Alert Patterns
- "500 Internal Server Error"
- "HTTP 500 rate increased"
- "5xx error spike"
- "Application error rate high"
- "Backend service failure"

## Severity Classification
- **Critical**: >5% of requests returning 500, or complete service down
- **High**: 1-5% error rate
- **Medium**: <1% error rate, isolated incidents

## Immediate Actions

### Step 1: Assess the Scope
```bash
# Check error rate in logs
tail -1000 /var/log/nginx/error.log | grep -c "500"

# Check application logs
tail -500 /var/log/application/app.log | grep -i "error\|exception"

# Check service health
curl -s http://localhost:8080/health
```

### Step 2: Common Causes

#### Database Connection Issues
```bash
# Check database connectivity
nc -zv database-host 5432

# Check connection pool
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check for long-running queries
psql -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query
         FROM pg_stat_activity WHERE state = 'active';"
```

#### Memory/Resource Issues
```bash
# Check application memory
ps aux | grep <app_name>

# Check for OOM in application logs
grep -i "outofmemory\|heap" /var/log/application/*.log
```

#### Dependency Failures
```bash
# Check downstream services
curl -s http://dependency-service/health

# Check for timeout patterns in logs
grep -i "timeout\|connection refused" /var/log/application/*.log
```

### Step 3: Mitigation

#### Restart Application (if safe)
```bash
# Graceful restart
systemctl restart application

# For containerized apps
kubectl rollout restart deployment/<app-name>
```

#### If Database Related
1. Check and increase connection pool limits
2. Kill long-running queries if safe
3. Restart database connection pools

#### If Dependency Related
1. Enable circuit breaker if available
2. Route traffic away from affected dependency
3. Contact dependent team

### Step 4: Verify Resolution
```bash
# Monitor error rate
watch -n 5 'tail -100 /var/log/nginx/access.log | grep -c "500"'

# Check application health
while true; do curl -s http://localhost:8080/health; sleep 5; done
```

## Root Cause Analysis Checklist
- [ ] Check recent deployments
- [ ] Review configuration changes
- [ ] Analyze error stack traces
- [ ] Check infrastructure changes
- [ ] Review traffic patterns

## Escalation Criteria
- Escalate to Development Team if:
  - Code bug identified
  - New deployment caused issue
  - Complex application logic failure
- Escalate to Database Team if:
  - Database performance issues
  - Connection pool exhaustion
- Escalate to Platform Team if:
  - Infrastructure-related cause
  - Multiple services affected

## Prevention
- Implement comprehensive error handling
- Set up circuit breakers for dependencies
- Monitor error rates proactively
- Implement canary deployments
