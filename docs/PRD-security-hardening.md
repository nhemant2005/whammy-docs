# Security Hardening — WhammyDocs

**Status:** Draft | **Priority:** High | **Label:** `ready-for-agent`

---

## Problem Statement

WhammyDocs is currently deployed at `whammydocs.duckdns.org` with a publicly accessible FastAPI backend, a DeepSeek API key in the environment, and zero authentication or rate limiting on any endpoint. Anyone who discovers the URL can upload arbitrary `.zip` files and trigger DeepSeek API calls paid for by the developer, potentially costing hundreds of dollars per hour in API fees. The session handling, file extraction, and nginx configuration also lack basic hardening measures.

---

## Solution

Hardening WhammyDocs across four layers:

1. **Nginx layer** — add authentication, rate limiting, and input size governance
2. **Application layer** — add per-session API spending caps, zip bomb protection, and file-level security validation
3. **Secret management** — eliminate plaintext credential exposure in scripts and disk
4. **Observability** — add audit logging so abuse is detectable

---

## User Stories

1. As the developer, I want all API endpoints protected by basic authentication, so that only authorized users can upload files and trigger DeepSeek API calls.
2. As the developer, I want strict rate limiting on upload endpoints, so that automated abuse cannot exhaust my API budget.
3. As the developer, I want the application to reject zip bombs and path traversal attacks during extraction, so that my VPS disk and memory cannot be exhausted by a malicious upload.
4. As the developer, I want a per-session maximum spending cap on DeepSeek API calls, so that even a single authorized upload cannot burn through my API budget.
5. As the developer, I want DuckDNS credentials and the DeepSeek API key stored with restricted permissions (owner-read-only) and never logged or exposed in error messages.
6. As the developer, I want structured audit logging for every upload and DeepSeek API call, so that I can identify abuse after the fact.
7. As the developer, I want the upload size limit reduced and validated at both nginx and application layers, so that large payloads are rejected before they consume resources.
8. As the developer, I want session directories cleaned up automatically after a timeout, so that abandoned sessions do not accumulate on disk.

---

## Implementation Decisions

### Modules to Build

#### 1. `middleware/auth.py` — Nginx basic auth integration

Nginx-level `auth_basic` is the simplest first line of defence. The setup script will:

- Generate a `.htpasswd` file using `openssl passwd` or `htpasswd`
- Add `auth_basic` and `auth_basic_user_file` directives to the nginx site config
- Reload nginx

_Future improvement:_ Replace with OAuth or API-key-based auth. For now, single shared password is acceptable for a hackathon/side project.

#### 2. `middleware/rate_limit.py` — Nginx rate limiting

Nginx `limit_req_zone` on the `/upload` and `/upload-sample` endpoints:

- Zone: 10MB shared memory
- Rate: 5 requests per minute per IP
- Burst: 10 (allows brief spikes)
- `nodelay` for the first request, delay excess

Add to nginx config:
```nginx
limit_req_zone $binary_remote_addr zone=upload:10m rate=5r/m;

location /upload {
    limit_req zone=upload burst=10 nodelay;
    # ... existing proxy config
}
```

#### 3. `middleware/security.py` — Zip bomb and path traversal validation

A new validation layer extracted from `main.py`'s upload handler:

**Zip bomb detection (before extraction):**
- Reject if uncompressed size (calculated from `zipfile.ZipInfo.file_size` sum) exceeds 500MB
- Reject if file count exceeds 10,000 entries
- Reject if any single file's uncompressed size exceeds 100MB

**Path traversal protection (during extraction):**
- After extraction, verify every extracted file's resolved path starts with `session_dir`
- Reject extraction if any path attempts `../` escape
- Reject symlinks in zip (`ZipInfo.external_attr` symlink bit check)

**File type allowlist:**
- Only extract files with extensions in: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.md`, `.json`, `.yaml`, `.yml`, `.toml`, `.txt`, `.html`, `.css`, `.rs`, `.go`, `.java`, `.cpp`, `.c`, `.h`, `.rb`, `.php`, `.sh`, `.sql`, `.cfg`, `.ini`, `.env.example`, `.gitignore`, `.dockerfile`, `.editorconfig`
- Silently skip (do not extract) all other file types
- Flag a warning in the session log for skipped files

#### 4. `middleware/cost_control.py` — Per-session API spending cap

A decorator or middleware on the DeepSeek API call path:

- Track cumulative token usage per `session_id` in memory (a dict with expiry)
- Reject generation if cumulative cost exceeds **$0.50** (approximately 1M input tokens on DeepSeek Flash)
- Return a clear error: "Session API budget exceeded. Start a new session."
- Reset on server restart (acceptable for a side project; persistent counters are out of scope)

#### 5. `middleware/audit.py` — Structured audit logging

A logging module that writes to a rotating file at `/var/log/whammy/audit.log`:

```json
{"timestamp": "...", "event": "upload.start", "session_id": "...", "client_ip": "...", "file_size": 12345, "file_count": 42}
{"timestamp": "...", "event": "upload.complete", "session_id": "...", "api_calls": 5, "total_tokens": 25000, "estimated_cost": 0.0125}
{"timestamp": "...", "event": "auth.failure", "client_ip": "..."}
```

- Log rotation via `logrotate` daily, keep 30 days
- Logs are readable only by `whammy` user and `adm` group (mode `640`)

#### 6. Session cleanup

A background task (FastAPI `lifespan` or a simple `asyncio.create_task`) that:

- Runs every 15 minutes
- Deletes session directories in `/tmp/whammy-*/` older than 2 hours
- Logs cleanup count

### Nginx config changes (summary)

| Directive | Current | Proposed |
|-----------|---------|----------|
| `client_max_body_size` | 50M | 20M |
| `proxy_read_timeout` | 600s | 300s |
| `auth_basic` | absent | "WhammyDocs" with `.htpasswd` |
| `limit_req` | absent | 5r/m on `/upload`, burst 10 |
| SSL | ✅ Let's Encrypt | ✅ (retain) |

### `.env` permissions

Current: `-rw-r--r-- whammy whammy` (world-readable)
Proposed: `-rw------- whammy whammy` (owner read/write only)

---

## Testing Decisions

### What makes a good test

- Tests validate **external behaviour** (the endpoint returns 401 when unauthenticated, rejects oversized zips, rejects traversal attempts)
- Tests do not mock the filesystem unnecessarily — use `tempfile.TemporaryDirectory` for extraction tests
- Cost control tests use fake token counts, not real API calls

### Modules to test

| Module | Test priority | What to test |
|--------|--------------|--------------|
| `middleware/security.py` | **Critical** | Zip bomb rejection, traversal rejection, symlink rejection, file type filtering |
| `middleware/cost_control.py` | **High** | Cap enforcement, reset on new session, edge case at exact limit |
| Upload endpoint (`main.py` `/upload`) | **High** | Rejection flow (auth → rate limit → size → zip validation), happy path still works |
| `middleware/audit.py` | **Medium** | Log format, rotation, permissions |

### Prior art

- Existing tests in `tests/test_upload_endpoint.py` can be extended with auth headers
- The existing `_50MB` constant test in `main.py` line 70 is prior art for rejection logic

---

## Out of Scope

- User accounts, registration, or OAuth (single shared password is sufficient)
- Persistent cost tracking across server restarts (resets are acceptable)
- Frontend-level security measures (CSP, XSS hardening — the app is HTMX/Jinja2 with no user-generated content rendering)
- Containerization / Docker (the app runs directly on the VPS)
- Cloudflare Tunnel migration (documented separately as future enhancement)
- HTTPS certificate management (already handled by Certbot)

---

## Further Notes

- The `.env` file at `/var/www/whammy-docs/.env` should be verified after deployment to ensure `chmod 600` was applied
- The DuckDNS token at `/var/www/duckdns/duck.sh` should also be locked to `chmod 700` on the directory (verify this is already the case)
- After deploying, test the full flow: authenticated upload → generation → preview → download
- The rate limit value (5r/m) is conservative. If the developer needs higher throughput for demo purposes, it can be relaxed to 10r/m. This is a deliberate starting point to prevent abuse
- All changes should be applied first to the local clone at `/root/whammy-docs/` for git tracking, then synced to `/var/www/whammy-docs/` via rsync, followed by `systemctl restart whammy-docs` and `systemctl reload nginx`
