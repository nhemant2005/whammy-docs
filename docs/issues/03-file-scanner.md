# Issue 3 — File scanner + section→file mapping

**Label:** ready-for-agent  
**Blocked by:** #2  
**User stories:** US 12, 14, 17

## What to build

After extraction, walk the session directory and produce a `mapping.json` file that maps each doc section to the relevant source files. Apply a universal ignore list. Detect and skip binary files. Use path-pattern matching (not language detection) to assign files to sections.

**Ignore list:** `node_modules/`, `__pycache__/`, `.git/`, `venv/`, `env/`, `dist/`, `build/`, `*.pyc`, `*.class`, `*.lock`, `package-lock.json`, `yarn.lock`, `Pipfile.lock`, and any file that fails UTF-8 decoding.

**Section→file patterns:**
- API Reference → `routes/`, `controllers/`, `api/`, `views/`, `*router*`, `*endpoint*`, `*handler*`
- Getting Started → `requirements.txt`, `package.json`, `Pipfile`, `go.mod`, `*.env.example`, top-level `README*`
- Deployment → `Dockerfile`, `docker-compose*`, `.github/workflows/`, `nginx.conf`
- Architecture → directory tree only (no file content)
- README → top-level files + detected entry point

## Acceptance criteria

- [ ] `mapping.json` written to session folder after upload
- [ ] No files from the ignore list appear in any mapping
- [ ] Binary files (images, compiled artifacts) are excluded
- [ ] A FastAPI project correctly maps route files to API Reference
