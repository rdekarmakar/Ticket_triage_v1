# Disk Full Alert Runbook

## Overview
This runbook covers procedures for handling disk space alerts when a server's disk usage exceeds threshold limits.

## Alert Patterns
- "Disk usage above 90%"
- "Filesystem full"
- "No space left on device"
- "Disk space critical"

## Severity Classification
- **Critical**: >95% usage or /var/log full
- **High**: 90-95% usage
- **Medium**: 80-90% usage

## Immediate Actions

### Step 1: Identify the Problem
```bash
# Check disk usage
df -h

# Find largest directories
du -sh /* 2>/dev/null | sort -hr | head -20

# Check for large log files
find /var/log -type f -size +100M -exec ls -lh {} \;
```

### Step 2: Quick Cleanup Options

#### Clear Log Files
```bash
# Truncate large log files (keeps file handle)
truncate -s 0 /var/log/large-log-file.log

# Clear old journal logs
journalctl --vacuum-time=3d
journalctl --vacuum-size=500M
```

#### Remove Old Packages
```bash
# Debian/Ubuntu
apt-get autoremove
apt-get clean

# RHEL/CentOS
yum autoremove
yum clean all
```

#### Remove Docker Artifacts
```bash
# Remove unused Docker resources
docker system prune -af
docker volume prune -f
```

### Step 3: Identify Root Cause
- Check if specific application is generating excessive logs
- Review log rotation configuration
- Check for core dumps or crash files
- Review database growth patterns

## Escalation Criteria
- Escalate to Storage Team if:
  - Disk cannot be cleaned below 85%
  - Problem recurs within 24 hours
  - Production database disk is affected

## Prevention
- Set up log rotation with appropriate retention
- Configure monitoring alerts at 80% threshold
- Schedule regular cleanup jobs
