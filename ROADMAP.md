# ROADMAP.md - All-Url-Uploader

## Technical Lifecycle Strategy

### Dependency Management
- Pin all dependencies with exact versions in `uv.lock` (already done)
- Monthly dependency audit using `pip-audit` or `safety`
- Quarterly major version upgrades with changelog review
- Automated CI checks for dependency vulnerabilities (GitHub Actions already configured)

### Architecture Evolution
- **Phase 1 (Current)**: Monolithic bot with file-based state, SQLite analytics, Flask dashboard
- **Phase 2**: Extract analytics into async background tasks; add Redis for caching/rate limiting
- **Phase 3**: Microservice split - separate download worker, upload worker, API gateway
- **Phase 4**: Kubernetes deployment with horizontal scaling

### Code Quality Standards
- Maintain 80%+ test coverage
- Enforce type hints on all new code
- Run pylint + mypy in CI
- Security scanning with bandit (already configured)
- Code review required for all PRs

### Database Migration Strategy
- Use Alembic for schema versioning
- Backward-compatible migrations only
- Test migrations on staging before production
- Rollback scripts for every migration

### Monitoring & Observability
- Structured JSON logging for production
- Prometheus metrics endpoint
- Grafana dashboards for system health
- Alerting for error rates, queue depth, disk space

## Product Roadmap (Telegram-Optimized)

### P0 - Critical (Next Sprint)
1. **Inline Mode Support** - Allow users to search and share downloads inline in any chat
2. **Batch URL Processing** - Accept multiple URLs in one message, process sequentially
3. **Download Resume** - Resume interrupted downloads using HTTP Range headers
4. **File Size Pre-check** - Show estimated size before download, warn if >2GB

### P1 - High Priority (1-2 Months)
5. **Custom Upload Captions** - Let users set custom captions via `/caption` command
6. **Playlist Support** - Download entire YouTube playlists as zip
7. **Format Presets** - Save preferred format per user (e.g., always 720p)
8. **Progress in Chat** - Edit original message instead of separate status message
9. **Auto-delete** - Option to auto-delete source message after upload
10. **Multi-language** - i18n support for bot messages

### P2 - Medium Priority (3-6 Months)
11. **Cloud Storage Integration** - Upload to Google Drive/Dropbox instead of Telegram
12. **Scheduled Downloads** - Queue downloads for off-peak hours
13. **Webhook Mode** - Switch from polling to webhooks for better scalability
14. **Admin Panel in Bot** - `/stats`, `/ban`, `/unban` commands for admins
15. **User Quotas** - Daily download limits per user to prevent abuse
16. **Thumbnail Auto-generation** - Extract thumbnail from video automatically

### P3 - Low Priority (6-12 Months)
17. **AI Content Detection** - Detect and flag NSFW content
18. **Subtitle Extraction** - Download and attach subtitles
19. **Audio Normalization** - Normalize audio levels during processing
20. **Video Compression** - Compress large videos to fit Telegram limits
21. **Streaming Upload** - Stream download directly to Telegram without intermediate file
22. **Multi-bot Support** - Run multiple bot instances from one codebase

### Technical Debt Items
- [ ] Replace file-based request state with Redis/PostgreSQL
- [ ] Implement proper async file I/O (aiofiles) throughout
- [ ] Add connection pooling for HTTP clients
- [ ] Add bounded concurrency with semaphores
- [ ] Implement subprocess timeouts for yt-dlp
- [ ] Add comprehensive integration tests
- [ ] Migrate to async database driver (aiosqlite/asyncpg)

### Scalability Targets
| Metric | Current | 6 Month | 12 Month |
|--------|---------|---------|----------|
| Concurrent users | ~10 | ~100 | ~1000 |
| Jobs/hour | ~50 | ~500 | ~5000 |
| Storage | Local disk | S3-compatible | Distributed |
| Uptime | 99% | 99.5% | 99.9% |
