# CivicLens — DevOps Lab Project Report

**Title:** CivicLens: A Civic Issue Reporting Platform with Docker & Jenkins CI/CD
**Domain:** Civic Tech / GovTech (Smart City)
**Stack:** Python Flask 3.0 · SQLite · Leaflet Maps · Docker + Compose · Jenkins · pytest

---

## 1. Aim & Objectives

**Aim:** Build a minimal, real-world civic reporting application and demonstrate a complete DevOps pipeline (code → test → containerize → CI/CD → deploy).

**Objectives:**
1. Solve a genuine problem: hyperlocal civic complaints lack an easy, transparent channel.
2. Deliver a working CRUD app with one differentiating feature (live map + status workflow + upvote prioritization).
3. Containerize with Docker (reproducible anywhere) and automate build/test/deploy with Jenkins.
4. Prove quality with automated tests gating the pipeline.

**Scope (deliberately minimal):** Single service + file DB. No auth, no payments, no microservices — complexity is in the *pipeline*, not the app, as the lab requires.

---

## 2. Problem Statement

Potholes, overflowing garbage, dead streetlights, and water leaks persist because:
- Reporting means phone calls / long forms with no tracking ID.
- Citizens can't see if others already reported the same issue (duplicates, apathy).
- No public prioritization — urgent issues drown in noise.
- No transparency on resolution (Open? Fixed? Ignored?).

**Users:** Citizens (reporters/upvoters), ward admins (status updaters), evaluators (demo audience).

---

## 3. System Architecture

```
┌─────────────┐      HTTP/JSON       ┌──────────────────────┐
│   Browser   │ ◄──────────────────► │   Flask (app.py)     │
│ HTML/CSS/JS │                      │  REST API + Jinja    │
│ Leaflet map │                      └──────┬───────┬───────┘
└─────────────┘                             │       │
                                     SQLite │       │ ./uploads
                                 (civiclens │       │ (photos)
                                  .db file) │       │
                                            ▼       ▼
                                     ┌──────────────────────┐
                                     │  Docker container    │
                                     │  gunicorn :5000      │
                                     │  VOLUME: /app/data   │
                                     │  VOLUME: /app/uploads│
                                     └──────────────────────┘
                                              ▲
                         Jenkins: Checkout → Test → Build → Deploy
```

**Data model (`issues` table):** `id, title, description, category, latitude, longitude, address, status, upvotes, image_path, created_at, updated_at`

**Request flow (create):** Form/multipart → Flask validation → optional image save → SQLite INSERT → JSON 201 → frontend re-fetches grid + stats.

---

## 4. Modules & Implementation

| Module | File | Responsibility |
|--------|------|----------------|
| Backend API | `app.py` (~300 lines) | 9 endpoints, validation, SQLite init, upload handling (5MB cap, extension filter) |
| UI shell | `templates/index.html` | Hero + stats, filters, grid, map div, 3 modals (report/detail/about) |
| Styling | `static/css/style.css` | Design system (teal civic theme, cards, badges, responsive) |
| Client logic | `static/js/app.js` | Fetch API, debounced search, Leaflet markers, modals, upvote/status actions |
| Tests | `tests/test_app.py` | 14 pytest cases using temp DB (no fixture pollution) |
| Demo data | `seed_demo.py` | 6 Pune-based issues with varied status/votes for presentation |

**Key design decisions:**
- SQLite over Postgres: zero-ops for lab; `DATABASE_PATH` env makes it swappable without code change (compose points it at a volume).
- Vanilla JS over React: no build step → Dockerfile stays 15 lines of logic, Jenkins needs no npm stage.
- Multipart + JSON support on `POST /api/issues`: file upload from UI, JSON from curl/tests.

---

## 5. DevOps Pipeline (the core of this submission)

### 5.1 Containerization

**Dockerfile** (`python:3.11-slim`): installs curl (healthcheck) → pip layer (cached) → copies app → `gunicorn -b 0.0.0.0:5000 app:app` with `HEALTHCHECK /api/health`.

**docker-compose.yml:** one service `app`, port `5000:5000`, named volume `civiclens-data` for DB, bind mount `./uploads` for photos, `restart: unless-stopped`, compose-level healthcheck.

This proves: *build once, run anywhere* — `docker compose up -d --build` reproduces the exact demo environment on any machine.

### 5.2 CI/CD (Jenkinsfile)

```
stage('Checkout')  → checkout scm
stage('Install')   → pip install -r requirements.txt
stage('Test')      → pytest tests/ -v   [GATE: fail = no build]
stage('Build')     → docker build -t civiclens:<BUILD_NUMBER> + :latest
stage('Deploy')    → compose down → compose up -d --build → curl /api/health
post { success/failure/always }
```

**DevOps concepts demonstrated:** automated testing as a quality gate, immutable image per build (`BUILD_NUMBER` tag), declarative redeploy, health verification, separation of state (volumes) from code (image).

### 5.3 How to run the pipeline (examiner steps)

1. Start Docker Desktop → `docker --version` responds.
2. `docker compose up -d --build` → open `http://localhost:5000` → *(app live)*.
3. `python -m pytest tests/ -v` → *14 passed*.
4. In Jenkins: New Pipeline job → repo URL → Build Now → console shows all 5 stages green → app redeployed.
5. Push a commit (e.g., edit title) → webhook (optional) rebuilds automatically.

---

## 6. Testing

| Strategy | Detail |
|----------|--------|
| Unit/API | 14 pytest tests: health, create success, 3 validation failures, list, category filter, search, status update + invalid rejection, double-upvote, delete + 404-after-delete, stats aggregation, single-not-found |
| Isolation | Each test uses `tempfile` DB — no cross-test pollution |
| Live E2E | Manual cycle via HTTP: create → get → patch status → upvote → stats → delete → stats=0 (verified 2026-10-13, all green) |
| Frontend | Title + brand string + HTML length check via HTTP |
| Pipeline gate | Jenkins `Test` stage fails the build on any test failure |

---

## 7. Results & Screenshots (what to capture for submission)

1. Homepage hero with stats (seed data loaded via `python seed_demo.py`)
2. Grid view with category pills + filters
3. Map view with 6 color-coded markers + popup
4. Report modal filled + success toast
5. Detail modal with status buttons
6. `pytest` output: `14 passed`
7. `docker compose ps` + `/api/health` JSON
8. Jenkins Blue Ocean / console: 5 green stages

---

## 8. Limitations & Future Work

- **Now:** single-node SQLite, no auth (anyone can change status/delete), no duplicate detection, map is display-only (no draw-to-report).
- **Next (if asked in viva):** Postgres + Alembic migrations; simple admin token for status/delete; keyword+distance auto-match for duplicates; Prometheus `/metrics` + Grafana dashboard; GitHub webhook + Docker Hub push stage; Nginx reverse proxy + HTTPS.

---

## 9. Conclusion

CivicLens meets the lab brief precisely: **unique** (civic tech, not a store clone), **real-world** (municipal reporting), **minimal complexity** (CRUD + map + upvote), and **fully DevOps** (Dockerized, Jenkins-gated, tested, one-command deploy). It demos well in 2 minutes and reads well on a resume.

---

## 10. Appendix — Viva Q&A (prepare these)

**Q: Why not MongoDB/Postgres?**
A: SQLite needs zero setup and the access pattern is single-node CRUD. `DATABASE_PATH` env abstraction means we can swap to Postgres without touching routes — and the Docker volume already separates state from image.

**Q: What happens if tests fail in Jenkins?**
A: The `Test` stage exits non-zero → pipeline stops → no Docker build, no deploy. Bad code never reaches production. That's the quality gate.

**Q: How is Docker different from just running `python app.py`?**
A: Docker freezes OS + Python + deps + code into an immutable image. It runs identically on my laptop, the lab PC, or a cloud VM. Volumes keep data across redeploys.

**Q: Where is the "DevOps" beyond Docker?**
A: Jenkins automates the whole lifecycle on every commit: checkout → install → test-gate → versioned image build → zero-manual-step redeploy + healthcheck. Plus `.dockerignore`/layer caching for fast builds.

**Q: Why is this unique vs E-commerce clones?**
A: Clones rehearse tutorials; CivicLens addresses Smart-City governance — photo+GPS evidence, public prioritization via upvotes, transparent Open→Resolved tracking. Different domain, real stakeholders, better story.

**Q: Single container — isn't that too simple?**
A: Intentionally: the lab grades the *pipeline*, not microservice sprawl. One stateless image + externalized state (volumes) is exactly what production best practice prescribes at this scale.
