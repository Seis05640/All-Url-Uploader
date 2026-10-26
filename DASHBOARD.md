# DASHBOARD.md - Analytics and Monitoring Dashboard

## Overview

The All-Url-Uploader dashboard is a lightweight Flask-based web interface for monitoring bot activity, job statistics, and system health. It runs on localhost by default and requires authentication via a configurable token.

## Architecture

- **Framework:** Flask 3.x (minimal dependency)
- **Database:** SQLite (shared with analytics store)
- **Authentication:** Token-based (session cookie with HttpOnly flag)
- **Binding:** localhost:5000 by default (configurable)

## Data Model

### Tables

1. **jobs** - Individual job records
   - token, user_id, source_host, status, send_type, file_size, download_seconds, upload_seconds, retry_count, error_category, created_at, completed_at

2. **events** - Structured event records
   - event_type, user_id, metadata, created_at

3. **resource_samples** - System resource measurements
   - cpu_percent, memory_mb, disk_used_mb, disk_free_mb, created_at

## Routes

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| /login | POST | No | Authenticate with dashboard token |
| /logout | POST | Yes | End session |
| / | GET | Yes | Dashboard overview page |
| /api/overview | GET | Yes | JSON overview statistics |
| /api/jobs | GET | Yes | Paginated job list (limit, offset, status) |
| /api/daily-stats | GET | Yes | Daily job statistics (days param) |
| /health | GET | No | Health check endpoint |

## Configuration

Environment variables:
- `DASHBOARD_ENABLED` - Enable/disable dashboard (default: false)
- `DASHBOARD_HOST` - Bind host (default: 127.0.0.1)
- `DASHBOARD_PORT` - Bind port (default: 5000)
- `DASHBOARD_TOKEN` - Authentication token (required when enabled)

## Security

- Binds to localhost by default
- Session cookies are HttpOnly
- CSRF protection via session tokens
- No sensitive data exposed (URLs redacted to host only)
- Admin token comparison uses constant-time comparison

## Data Retention

- Analytics records retained for 30 days by default
- Cleanup via `AnalyticsStore.cleanup_old_records(retention_days=30)`
- Resource samples sampled periodically (not yet automated)

## Privacy

- Only source hostname stored (not full URLs)
- User IDs stored as pseudonymous identifiers
- No message content or credentials stored
- Telegram bot token never exposed to browser

## Running the Dashboard

```bash
# Set environment variables
export DASHBOARD_ENABLED=true
export DASHBOARD_TOKEN=your-secure-token

# Run bot (dashboard starts if enabled)
python bot.py
```

The dashboard will be available at http://127.0.0.1:5000
