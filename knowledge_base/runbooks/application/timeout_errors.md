# Timeout Errors Runbook

## Overview
This runbook covers procedures for handling timeout errors including API timeouts, request timeouts, and service-to-service communication timeouts.

## Alert Patterns
- "Request timeout"
- "Gateway timeout (504)"
- "Connection timeout"
- "Read timeout"
- "Service timeout"
- "Upstream timeout"

## Severity Classification
- **Critical**: >10% of requests timing out
- **High**: 5-10% timeout rate
- **Medium**: <5% timeout rate

## Immediate Actions

### Step 1: Identify Timeout Source
```bash
# Check nginx/load balancer logs
grep -i "timeout\|504" /var/log/nginx/error.log | tail -50

# Check application logs
grep -i "timeout" /var/log/application/*.log | tail -50

# Check which endpoint is timing out
grep "504" /var/log/nginx/access.log | awk '{print $7}' | sort | uniq -c | sort -rn
```

### Step 2: Check System Resources
```bash
# CPU usage
top -bn1 | head -20

# Memory
free -h

# I/O wait
iostat -x 1 5

# Network connections
ss -s
netstat -an | grep ESTABLISHED | wc -l
```

### Step 3: Check Downstream Dependencies
```bash
# Response time to dependencies
time curl -s http://dependency-service/health

# Check dependency health
for svc in service1 service2 service3; do
  echo -n "$svc: "
  curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://$svc/health
done
```

### Step 4: Check Database Performance
```sql
-- PostgreSQL: Long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';

-- PostgreSQL: Waiting queries
SELECT * FROM pg_stat_activity WHERE wait_event_type IS NOT NULL;
```

### Step 5: Mitigation

#### If Resource Constrained
1. Scale up/out application instances
2. Implement caching for expensive operations
3. Optimize slow queries

#### If Dependency Slow
1. Enable circuit breaker
2. Increase timeout temporarily (if appropriate)
3. Route around slow dependency if possible

#### If Database Slow
```sql
-- Kill long-running query (PostgreSQL)
SELECT pg_terminate_backend(pid);

-- Add missing indexes
EXPLAIN ANALYZE <slow_query>;
```

#### Quick Timeout Adjustment (temporary)
```bash
# Nginx upstream timeout
# In nginx.conf
proxy_read_timeout 120s;
proxy_connect_timeout 60s;
```

### Step 6: Verify Resolution
```bash
# Monitor response times
while true; do
  curl -s -o /dev/null -w "Time: %{time_total}s Code: %{http_code}\n" http://localhost/api/endpoint
  sleep 2
done

# Monitor timeout rate
watch -n 10 'tail -1000 /var/log/nginx/access.log | grep -c "504"'
```

## Root Cause Analysis
- Review slow queries
- Check for N+1 query problems
- Analyze third-party API latency
- Review connection pool settings
- Check for resource contention

## Escalation Criteria
- Escalate to Development Team if:
  - Code optimization needed
  - Query optimization required
- Escalate to Database Team if:
  - Database performance issues
  - Index optimization needed
- Escalate to Platform Team if:
  - Infrastructure scaling needed
  - Network latency issues

## Prevention
- Set appropriate timeout values
- Implement circuit breakers
- Use caching strategically
- Monitor response time percentiles
- Regular performance testing
- Implement async processing for long operations
