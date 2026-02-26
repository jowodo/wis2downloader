# Housekeep Manager Module

Celery tasks for housekeeping and maintenance operations in the WIS2 system.

## Overview

This module provides:
- Celery worker configuration with Redis backend
- Housekeeping tasks for cleaning, archiving, and maintaining system state
- Prometheus metrics for monitoring
- Workflow chains for task orchestration

## Documentation

- [Developer Guide](../../docs/developer-guide.adoc) - Architecture and code details
- [Admin Guide](../../docs/admin-guide.adoc) - Configuration and monitoring

## Entry Points

- `housekeep_manager_start` - CLI entry point for starting Celery worker

## Key Files

| File | Description |
|------|-------------|
| `worker.py` | Celery app configuration and worker startup |
| `tasks/housekeep.py` | Housekeeping and maintenance tasks |
| `workflows/__init__.py` | Task chain definitions |

## Tasks

### `housekeep_task`

Performs scheduled housekeeping operations such as cleaning up old data, archiving, and maintaining system health.

Features:
- Scheduled execution via Celery Beat
- Distributed locking to prevent concurrent operations
- Metrics collection for monitoring
- Customizable task workflows

### `archive_task`

Handles archiving of files and data as part of housekeeping routines.

- Automatic file organization by date

### `cleanup_task`

Removes obsolete or unnecessary files and records to maintain system efficiency.

Placeholder for additional post-housekeeping processing.
