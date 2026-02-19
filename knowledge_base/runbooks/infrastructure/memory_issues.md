# Memory Issues Alert Runbook

## Overview
This runbook covers procedures for handling memory-related alerts including high memory usage, OOM (Out of Memory) events, and memory leaks.

## Alert Patterns
- "Memory usage above 90%"
- "OOM killer activated"
- "Out of memory"
- "Swap usage high"
- "Memory leak detected"

## Severity Classification
- **Critical**: OOM killer activated or >95% memory usage
- **High**: 90-95% memory usage or swap >50%
- **Medium**: 80-90% memory usage

## Immediate Actions

### Step 1: Assess Memory State
```bash
# Overall memory usage
free -h

# Detailed memory info
cat /proc/meminfo

# Top memory consumers
ps aux --sort=-%mem | head -20

# Check for OOM events
dmesg | grep -i "oom"
journalctl -k | grep -i "oom"
```

### Step 2: Identify the Cause

#### Check Application Memory
```bash
# Memory by process
smem -tk

# Java heap usage (if applicable)
jcmd <PID> GC.heap_info

# Check memory maps
pmap -x <PID> | tail -5
```

#### Check for Memory Leaks
```bash
# Watch memory growth over time
watch -n 5 'ps -o pid,rss,cmd -p <PID>'

# Check for increasing resident memory
while true; do ps -o rss= -p <PID>; sleep 60; done
```

### Step 3: Mitigation Options

#### Quick Relief
```bash
# Clear page cache (safe)
sync; echo 3 > /proc/sys/vm/drop_caches

# Clear swap (if memory available)
swapoff -a && swapon -a
```

#### Application-Level
1. Trigger garbage collection if applicable
2. Restart memory-leaking service
3. Reduce application memory limits
4. Scale out to distribute load

#### If OOM Occurring
```bash
# Check what was killed
dmesg | grep -i "killed process"

# Restart affected services
systemctl restart <service_name>

# Adjust OOM score if needed
echo -1000 > /proc/<PID>/oom_score_adj  # Protect critical process
```

### Step 4: Verify Resolution
```bash
# Monitor memory after mitigation
watch -n 5 'free -h; echo "---"; ps aux --sort=-%mem | head -5'
```

## Root Cause Analysis
- Check for memory leaks in application code
- Review recent deployments
- Analyze traffic patterns
- Check configuration changes

## Escalation Criteria
- Escalate to Application Team if:
  - Confirmed memory leak
  - Restart doesn't resolve
  - Multiple instances affected
- Escalate to Platform Team if:
  - Kernel-level memory issues
  - Hardware suspected

## Prevention
- Implement memory limits in container/cgroup configuration
- Set up memory leak detection monitoring
- Regular application profiling
- Capacity planning reviews
