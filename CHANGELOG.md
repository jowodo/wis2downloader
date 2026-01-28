# WIS2 Downloader Refactor - Progress Log

## 2026-01-27

### Phase 1: Subscriber/Subscription-Manager Separation - COMPLETE

**Problem:** Refactor was left incomplete 2 months ago. Services wouldn't start due to missing imports and undefined variables.

**Fixed:**
- `modules/subscriber/setup.py` - Created with entry point `subscriber_start`
- `modules/subscriber/subscriber/__init__.py` - Added exports
- `modules/subscriber/subscriber/manager.py` - Added `from uuid import uuid4`
- `modules/subscriber/subscriber/command_listener.py` - Added `import os`, uses shared Redis client
- `modules/subscription_manager/subscription_manager/__init__.py` - Removed broken subscriber imports
- `modules/subscription_manager/subscription_manager/app.py` - Fixed delete endpoint, added COMMAND_CHANNEL
- `containers/subscriber/Dockerfile` - Created new Dockerfile for subscriber service
- `docker-compose.yaml` - Updated subscriber-france to use new Dockerfile

### Phase 2: Redis HA Improvements - COMPLETE

**Problem:** Duplicated Redis client code across modules, no single Redis fallback.

**Fixed:**
- `modules/shared/` - Created shared module with `redis_client.py`
- `modules/shared/shared/redis_client.py` - Centralized Redis client with Sentinel support and single Redis fallback
- Updated all modules to import from shared
- Updated all Dockerfiles to install shared module

### Redis Sentinel Failover - COMPLETE

**Problem:** Sentinel failover not working in Docker Compose due to hostname resolution issues causing repeated tilt mode.

**Root Cause:** When a container stops, Docker DNS removes its hostname. Sentinel's `resolve-hostnames yes` caused constant resolution failures and tilt mode re-entry, blocking failover.

**Solution:** Implemented static IPs for all Redis components.

**Changes:**
- `docker-compose.yaml` - Added `redis-net` network with subnet 172.28.0.0/16
  - redis-primary: 172.28.0.10
  - redis-replica-1: 172.28.0.11
  - redis-replica-2: 172.28.0.12
  - redis-sentinel-1: 172.28.0.20
  - redis-sentinel-2: 172.28.0.21
  - redis-sentinel-3: 172.28.0.22
- `containers/redis-sentinel/sentinel.conf` - Uses static IP instead of hostname:
  ```
  sentinel monitor redis-primary 172.28.0.10 6379 2
  sentinel down-after-milliseconds redis-primary 5000
  sentinel failover-timeout redis-primary 60000
  protected-mode no
  ```

**Result:** Failover completes in ~2 seconds.

### Subscriber Reconnection Fix - COMPLETE

**Problem:** After Redis failover, subscriber's command_listener didn't reconnect properly.

**Root Cause:** `pubsub` object created once in `__init__`, connection error handler just slept and continued without recreating pubsub or resubscribing.

**Fix:** Added `_reconnect()` method to `command_listener.py`:
```python
def _reconnect(self):
    """Recreate pubsub and resubscribe after connection failure."""
    try:
        self.pubsub.close()
    except Exception:
        pass
    self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
    self.pubsub.subscribe(self.channel)
    LOGGER.info(f"Reconnected and resubscribed to channel: {self.channel}")
```

**Result:** Subscriber auto-reconnects after failover.

---

## Pending Work (from tasks.md)

### Phase 3: Configuration Improvements
- [ ] Fix subscription storage (Redis only)
- [ ] Make cache blacklist configurable
- [ ] Improve Celery worker configuration
- [ ] Fix invalid JSON in transport options default

### Phase 4: Download Task Improvements
- [x] Improve file type detection
- [ ] Add STATUS_QUEUED constant
- [ ] Add centre_id to result dict
- [ ] Add dataset field to result
- [ ] Add media-type safe list validation

### Phase 5: Metrics Improvements
- [ ] Add wis2_ prefix to Prometheus metrics
- [ ] Simplify metrics labels
- [ ] Initialize Prometheus multiprocess mode properly

### Phase 6: Code Quality
- [ ] Remove commented/dead code
- [ ] Standardize logging
- [ ] Add type hints

### Phase 7: Environment & Docker
- [ ] Update default.env
- [ ] Clean up git status
