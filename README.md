# CivicLens — Civic Issue Reporter for Smart Cities

> **DevOps Lab Project** — Report potholes, garbage, broken streetlights with photo + GPS. Track status transparently: `Open → In-Progress → Resolved` on a live map.
> Not another store clone — this is **Civic Tech / GovTech**, a real Smart-City problem.

![Stack](https://img.shields.io/badge/Flask-3.0-teal) ![DB](https://img.shields.io/badge/SQLite-builtin-blue) ![Docker](https://img.shields.io/badge/Docker-ready-2496ED) ![Jenkins](https://img.shields.io/badge/Jenkins-pipeline_green-D24939) ![Tests](https://img.shields.io/badge/pytest-14_passed-green)

**Live status (verified):** Jenkins build **SUCCESS** — app deployed at `http://localhost:5000` (seeded with 8 demo reports), Jenkins open at `http://localhost:8080` — no login (local lab).

---

## 1. Problem & Solution

**Problem:** Civic issues (potholes, overflowing bins, dead streetlights, leaks) go unreported. Municipal helplines are slow, opaque, and not hyperlocal. Citizens have no easy way to report with proof + location, or track what happened after.

**Solution:** CivicLens — a sub-minute reporting app:
1. Citizen spots an issue → submits **title + photo + category + GPS + address**
2. Everyone sees it on a **live Leaflet map** + searchable list
3. Community **upvotes** to prioritize urgent issues
4. Admin updates **status** (Open → In-Progress → Resolved)
5. **Stats strip** shows filed / open / resolved counts

**One-line seminar pitch:** *"Mini FixMyStreet for our city — report in under a minute, track to resolution."*

---

## 2. Features

| # | Feature | Type |
|---|---------|------|
| 1 | Report issue (photo upload ≤5MB, GPS, category, address) | CREATE |
| 2 | List view with search, category pills, status filter, sort (newest/oldest/upvotes) | READ |
| 3 | Live Leaflet map with color-coded markers (brown Open / blue In-Progress / green Resolved) | READ |
| 3b | New-user guidance: 3-step how-it-works strip, first-visit hint bar (remembered), `?` tooltips on filters/sort/upvote | UX |
| 4 | Detail modal with full info + image | READ |
| 5 | Admin status update (Open / In-Progress / Resolved) | UPDATE |
| 6 | Upvote to prioritize (1 click → +1) | UPDATE |
| 7 | Delete issue (+ cleans up image file) | DELETE |
| 8 | Stats API + header counters (filed / open / resolved) | ANALYTICS |
| 9 | Server-side validation (title ≥3, desc ≥10, valid category/coords) | QUALITY |

---

## 3. Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | **Python Flask 3.0** | ~300 lines, perfect for lab, easy to test |
| Database | **SQLite** (file) / `DATABASE_PATH` env override | Zero-setup; Docker volume persists it |
| Frontend | HTML + custom CSS + vanilla JS + **Leaflet 1.9** maps | No build step; GOV.UK/FixMyStreet-inspired civic theme |
| Server (prod) | **Gunicorn** (2 workers) | Production WSGI inside Docker |
| Testing | **pytest** (14 tests) | Jenkins `Test` stage gate |
| DevOps | **Docker + Compose + Jenkins (in Docker)** | Full CI/CD pipeline |

---

## 4. Project Structure

```
.
├── app.py                 # Flask app: API + SQLite + upload handling
├── seed_demo.py           # Seeds 8 realistic demo issues (for seminar)
├── requirements.txt       # Flask, Flask-Cors, Werkzeug, gunicorn, pytest
├── Dockerfile             # python:3.11-slim → gunicorn, healthcheck
├── docker-compose.yml     # app + named volume + uploads bind mount
├── Jenkinsfile            # Checkout → Install → Test → Build → Deploy (sh/bat)
├── templates/
│   └── index.html         # UI shell (service header, filters, list, map, modals)
├── static/
│   ├── css/style.css      # Civic-service theme (solid colours, no gradients)
│   └── js/app.js          # Fetch API, list/map render, modals, upvote
├── tests/
│   └── test_app.py        # 14 pytest tests (health, CRUD, filters, validation)
├── uploads/               # Uploaded photos (gitignored, Docker volume)
├── docs/
│   └── PROJECT_REPORT.md  # Lab submission report (aim, architecture, pipeline, viva)
└── README.md              # This file
```

---

## 5. API Reference

Base URL: `http://localhost:5000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Frontend UI |
| `GET` | `/api/health` | Healthcheck → `{"status":"ok"}` |
| `GET` | `/api/issues?category=&status=&search=&sort=` | List + filter + search + sort |
| `POST` | `/api/issues` | Create (JSON or multipart with `image` file) |
| `GET` | `/api/issues/<id>` | Single issue |
| `PATCH` | `/api/issues/<id>/status` | Body `{"status":"Open"\|"In-Progress"\|"Resolved"}` |
| `POST` | `/api/issues/<id>/upvote` | +1 upvote |
| `DELETE` | `/api/issues/<id>` | Delete + remove image |
| `GET` | `/api/stats` | `{total, open, inProgress, resolved, byCategory}` |

**Create example (JSON):**
```bash
curl -X POST http://localhost:5000/api/issues \
  -H "Content-Type: application/json" \
  -d '{"title":"Pothole on MG Road","description":"Deep pothole near signal, dangerous for bikes.","category":"pothole","latitude":"18.5204","longitude":"73.8567","address":"MG Road, Pune"}'
```

---

## 6. Run Locally (no Docker)

```powershell
# 1. Install deps
pip install -r requirements.txt

# 2. Run dev server
python app.py
# → http://127.0.0.1:5000

# 3. (Optional) Seed demo data for presentation
python seed_demo.py

# 4. Run tests
python -m pytest tests/ -v
# → 14 passed
```

---

## 7. Run with Docker

> Requires **Docker Desktop running**.

```powershell
# Build + start (detached)
docker compose up -d --build

# Check health
curl http://localhost:5000/api/health

# Logs
docker compose logs -f app

# Stop
docker compose down
```

What compose does:
- Builds the `civiclens` image (Flask + gunicorn on :5000)
- Persists DB in named volume `civiclens-data` (`DATABASE_PATH=/app/data/civiclens.db`)
- Persists photos via `./uploads:/app/uploads` bind mount
- Healthcheck hits `/api/health` every 30s

---

## 8. Jenkins CI/CD Pipeline

`Jenkinsfile` stages (cross-platform: `sh` on Linux agents, `bat` on Windows):

```
Checkout → Install Dependencies → Test → Docker Build → Deploy
```

| Stage | What happens |
|-------|--------------|
| Checkout | `checkout scm` (repo, `main` branch) |
| Install | `pip install -r requirements.txt` |
| Test | `pytest tests/ -v` — **gate: any failure stops the pipeline** |
| Docker Build | `docker build -t civiclens:<BUILD_NUMBER>` + tag `latest` |
| Deploy | `compose down → compose up -d --build` → healthcheck **inside** the app container (`compose exec -T app curl …`) with retries |

**This repo's Jenkins (already installed, green builds):**
- URL: `http://localhost:8080` — **no login** (security disabled for the local lab)
- Job: `civiclens-pipeline` (Pipeline from SCM → this repo, `Jenkinsfile`)
- Jenkins itself runs in Docker (`jenkins/jenkins:lts`); the agent has Python 3, Docker CLI + Compose v2 via the host socket, and git + pipeline plugins
- Start it with `docker start jenkins`, then *Build Now* any time

**Why `compose exec` for the healthcheck?** The Jenkins agent runs in its own container, so its `localhost` is not the app. The check runs `curl` inside the app container over its real `localhost:5000` — portable to any Docker host.

See [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md) §5 for the full pipeline explanation + viva answers.

---

## 9. Test Report

```
14 passed (local Windows + Jenkins Linux agent, Python 3.11 and 3.13)
✓ health, create success, 3 validation rejections (title/category/coords)
✓ list, category filter, search
✓ status update + invalid-status rejection
✓ upvote (incl. double-upvote → 2), delete (+404 after), stats aggregation
```

Browser E2E also verified: report submit → detail → upvote → status change → live map markers (Pune tiles).

---

## 10. Why This Beats Classmates' Clones

| Classmates build | You build |
|------------------|-----------|
| Amazon/Netflix/Spotify clone (tutorial copy) | **Civic Tech** — original, Smart-City aligned |
| No real user | Every citizen + municipal worker is a user |
| Cart/checkout = fake complexity | Map + status workflow = *visible* complexity in demo |
| "What problem does it solve?" — awkward silence | "Potholes/garbage go unreported" — evaluator nods instantly |
| Same resume line as 50 others | "Built civic reporting platform with CI/CD" — stands out |

---

## 11. Resume Line (copy-paste)

> **CivicLens — Civic Issue Reporting Platform** | *Flask, SQLite, Leaflet, Docker, Jenkins*
> Built a Smart-City issue tracker (report with photo+GPS, live map, upvote prioritization, Open→Resolved workflow). Containerized with Docker, automated CI/CD via Jenkins (test-gated build → deploy, 3 green builds), 14 pytest tests, healthchecks + persistent volumes.

---

## 12. Demo Script (2-min seminar)

1. **Hook (15s):** "Who here has seen a pothole unfixed for months? Municipal helplines are black boxes."
2. **Report (30s):** Click *Report an issue* → fill → Submit → appears in list instantly.
3. **Map (20s):** Switch to *Map* → "every dot is a live complaint, colour = status."
4. **Engage (20s):** Upvote top issue → counter +1 → "community prioritizes, not just officials."
5. **Resolve (20s):** Open detail → change status to *In progress* → *Resolved* → header stats update.
6. **DevOps punch (15s):** "Every push runs Jenkins: tests → Docker build → redeploy. Same code runs on my laptop and any server via one `docker compose up`."

---

*Built for DevOps Lab — Flask + SQLite + Docker + Jenkins. Run anywhere with one command.*
