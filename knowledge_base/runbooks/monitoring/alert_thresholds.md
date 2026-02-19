# Alert Thresholds and Configuration

## Overview
This document defines standard alerting thresholds and guidelines for production monitoring.

## Infrastructure Alerts

### CPU Utilization
| Severity | Threshold | Duration | Action |
|----------|-----------|----------|--------|
| Warning | >70% | 5 min | Monitor |
| High | >85% | 5 min | Investigate |
| Critical | >95% | 3 min | Immediate action |

### Memory Utilization
| Severity | Threshold | Duration | Action |
|----------|-----------|----------|--------|
| Warning | >75% | 5 min | Monitor |
| High | >85% | 5 min | Investigate |
| Critical | >95% or OOM | 1 min | Immediate action |

### Disk Utilization
| Severity | Threshold | Duration | Action |
|----------|-----------|----------|--------|
| Warning | >70% | N/A | Plan cleanup |
| High | >85% | N/A | Cleanup required |
| Critical | >95% | N/A | Immediate cleanup |

### Network
| Metric | Warning | Critical |
|--------|---------|----------|
| Packet Loss | >1% | >5% |
| Latency | >100ms | >500ms |
| Bandwidth | >70% | >90% |

## Application Alerts

### HTTP Error Rates
| Severity | 5xx Rate | Duration | Action |
|----------|----------|----------|--------|
| Warning | >0.5% | 5 min | Monitor |
| High | >1% | 5 min | Investigate |
| Critical | >5% | 2 min | Immediate action |

### Response Time (p99)
| Severity | Threshold | Duration | Action |
|----------|-----------|----------|--------|
| Warning | >500ms | 5 min | Monitor |
| High | >1s | 5 min | Investigate |
| Critical | >5s | 2 min | Immediate action |

### Request Queue Length
| Severity | Threshold | Duration | Action |
|----------|-----------|----------|--------|
| Warning | >100 | 2 min | Monitor |
| High | >500 | 2 min | Scale up |
| Critical | >1000 | 1 min | Immediate scale |

## Database Alerts

### Connection Pool
| Severity | Threshold | Action |
|----------|-----------|--------|
| Warning | >70% utilized | Monitor |
| High | >85% utilized | Investigate |
| Critical | >95% utilized | Scale pool |

### Query Performance
| Severity | Slow Queries/min | Action |
|----------|------------------|--------|
| Warning | >10 | Review queries |
| High | >50 | Optimize |
| Critical | >100 | Immediate action |

### Replication Lag
| Severity | Lag | Action |
|----------|-----|--------|
| Warning | >5s | Monitor |
| High | >30s | Investigate |
| Critical | >60s | Failover consideration |

## Alert Routing

### By Severity
- **Critical**: Page on-call immediately, auto-create incident
- **High**: Notify on-call via Slack/Webex, create ticket
- **Warning**: Notify team channel, log for review

### By Time
- **Business Hours (9am-6pm)**: Full team notifications
- **After Hours**: On-call only for High/Critical
- **Weekends**: On-call only for Critical

## Alert Suppression Rules
1. Suppress during maintenance windows
2. Aggregate similar alerts (max 1 per 5 minutes)
3. Auto-resolve if condition clears for >10 minutes
4. Don't page for known issues with workarounds

## Runbook Links
Each alert should link to the appropriate runbook:
- CPU alerts → high_cpu.md
- Memory alerts → memory_issues.md
- Disk alerts → disk_full.md
- HTTP 5xx alerts → error_500.md
- Timeout alerts → timeout_errors.md
- Database alerts → database_connection.md
