# High CPU Usage Alert Runbook

## Overview
This runbook covers procedures for handling high CPU utilization alerts on production servers.

## Alert Patterns
- "CPU usage above 90%"
- "High CPU utilization"
- "CPU saturation detected"
- "Load average high"

## Severity Classification
- **Critical**: >95% sustained for >5 minutes
- **High**: 90-95% sustained
- **Medium**: 80-90% usage

## Immediate Actions

### Step 1: Identify CPU Consumers
```bash
# Top processes by CPU
top -bn1 | head -20

# Detailed process CPU usage
ps aux --sort=-%cpu | head -20

# Check load average
uptime

# Per-core CPU usage
mpstat -P ALL 1 5
```

### Step 2: Analyze the Cause

#### Check if Application Related
```bash
# Find application processes
pgrep -la <app_name>

# Check application threads
ps -eLf | grep <app_name>

# Check for runaway processes
ps aux | awk '$3 > 50 {print}'
```

#### Check for System Issues
```bash
# Check for kernel issues
dmesg | tail -50

# Check for I/O wait (can appear as CPU usage)
iostat -x 1 5

# Check for zombie processes
ps aux | grep Z
```

### Step 3: Mitigation Options

#### If Application Issue
1. Check application logs for errors
2. Restart application if safe
3. Scale horizontally if available
4. Enable rate limiting if applicable

#### If Runaway Process
```bash
# Reduce priority
renice +10 <PID>

# If necessary, terminate gracefully
kill -15 <PID>

# Force terminate only as last resort
kill -9 <PID>
```

### Step 4: Verify Resolution
```bash
# Monitor CPU after mitigation
watch -n 2 'top -bn1 | head -10'
```

## Root Cause Analysis
- Review deployment history
- Check for traffic spikes
- Analyze application performance metrics
- Review cron jobs or scheduled tasks

## Escalation Criteria
- Escalate to Application Team if:
  - CPU remains high after basic mitigation
  - Application restart doesn't help
  - Related to recent deployment
- Escalate to Platform Team if:
  - Affects multiple servers
  - Kernel or system-level issue suspected

## Prevention
- Set up auto-scaling policies
- Implement request throttling
- Monitor application performance proactively
- Review capacity planning regularly
