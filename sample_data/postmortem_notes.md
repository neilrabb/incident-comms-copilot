# Incident 2024-09-12: Auth Service Degradation

## Timeline
- 14:15 UTC — Deploy of auth-service v2.41.0 began (Redis 6→7 migration)
- 14:25 UTC — Deploy fully rolled out to us-east-1
- 14:30 UTC — Latency spike detected, error rate climbing
- 14:32 UTC — First alert fired (p99 > 5s)
- 14:36 UTC — SEV-1 declared
- 14:40 UTC — Incident Commander assigned (Dave P.)
- 14:52 UTC — Decision to rollback
- 15:42 UTC — Rollback to v2.40.3 complete
- 15:48 UTC — Metrics recovering
- 16:30 UTC — Incident resolved

## Impact
- Duration: ~2 hours (14:30–16:30 UTC)
- Affected services: login, SSO, session validation, authenticated API calls
- Affected region: us-east-1 only
- Customer impact: users unable to log in or experienced slow/failed requests. Approximately 12 enterprise orgs reported SSO failures. Session counts dropped from 142k to 78k during peak impact.

## Root Cause
The v2.41.0 release migrated the session store client from Redis 6 to Redis 7. The new Redis 7 client library uses a lower default connection pool maximum (10 vs 50). Under production load, the pool was exhausted within minutes, causing auth-service pods to queue and timeout on Redis operations.

## Resolution
Rolled back to v2.40.3 (previous Redis 6 client). Service recovered within ~10 minutes of rollback completion.

## Action Items
- [ ] Update Redis 7 client config to set explicit pool size matching production requirements
- [ ] Add connection pool utilization to canary deploy health checks
- [ ] Load test Redis 7 migration in staging with production-scale traffic
