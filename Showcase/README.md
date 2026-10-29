# CivicLens — Showcase Pack

Final evidence for the DevOps lab presentation. Everything here was captured from the live
project running on this machine: Flask app on `http://localhost:5000`, Jenkins on
`http://localhost:8080` (no login), Docker Desktop on the host.

**Status at capture:** Jenkins build **#10 SUCCESS** · **14/14 pytest tests** · app healthy
(`/api/health` → `status: ok`) · 8 seeded reports.

---

## 1. Suggested presentation order

| Step | Asset | What it proves |
|------|-------|----------------|
| 1 | `01-app-home.png` → `02-app-home-full.png` | The live civic reporting UI, stats and all 8 reports |
| 2 | `03-app-map.png` → `04-app-detail.png` | Leaflet map, status-coloured pins, report details |
| 3 | `05-app-report-form.png` → `06-app-search-filter.png` → `07-app-about.png` | Report workflow, search/filter, project scope |
| 4 | `08-docker-containers.png` → `09-docker-images.png` | App + Jenkins containers running; built image and base images |
| 5 | `10-jenkins-dashboard.png` → `11-jenkins-job.png` → `12-jenkins-build.png` | Jenkins job, build history and build #10 summary |
| 6 | `13-jenkins-console-top.png` → `14-jenkins-tests.png` → `15-jenkins-deploy.png` | Checkout → 14 tests passed → Docker build → deploy → **SUCCESS** |
| 7 | `CivicLens-Full-Demo.mp4` | The whole story in one 60-second video (title cards + app + pipeline) |

If time is short, play `CivicLens-Full-Demo.mp4`; for a live walkthrough, use the two raw
recordings and the screenshots in the order above.

---

## 2. Screenshots

All app/Jenkins screenshots are **1600 × 1000**; Docker Desktop screenshots are
**1920 × 1080**. `02-app-home-full.png` is a full-page capture at **1600 × 1312**.

| File | Description |
|------|-------------|
| `01-app-home.png` | Landing page: hero, live stats (8 filed / 5 open / 2 resolved) and report cards |
| `02-app-home-full.png` | Full-page view of all 8 seeded reports plus the footer |
| `03-app-map.png` | Live Leaflet map with status-coloured markers and an open report popup |
| `04-app-detail.png` | Report detail modal with description, location, upvotes and status |
| `05-app-report-form.png` | Report form filled with title, category, description, address and coordinates |
| `06-app-search-filter.png` | Search for “drain” → two matching reports |
| `07-app-about.png` | About modal: problem, solution, stack and “14 tests passing” |
| `08-docker-containers.png` | Docker Desktop → Containers: `jenkins` and `civiclens-app` running, plus the `civiclens-pipeline` Compose group |
| `09-docker-images.png` | Docker Desktop → Images: per-build `civiclens:10` (plus tags 7/8/9/latest), Compose image `civiclens-pipeline-app` (235.63 MB), and base images — captured before the image cleanup |
| `10-jenkins-dashboard.png` | Jenkins dashboard: job green, last success **#10**, last duration 10 s |
| `11-jenkins-job.png` | Job page: description, permalinks and build history (#10 latest) |
| `12-jenkins-build.png` | Build #10 summary: success, commit, repository, “Took 10 sec” |
| `13-jenkins-console-top.png` | Console start: SCM checkout, commit `a4d386d`, pipeline stages begin |
| `14-jenkins-tests.png` | Console quality gate: all **14 tests PASSED**, `14 passed in 0.37s` |
| `15-jenkins-deploy.png` | Console deploy: image build, container start, health JSON, **Finished: SUCCESS** |

### Build-history note

- Builds **#3, #4, #5, #7, #8, #9 and #10** are green; **#10** is the latest successful run shown throughout.
- Builds **#1–#2** are the two early failures documented in
  [`../docs/PROJECT_REPORT.md`](../docs/PROJECT_REPORT.md) §5.3: a cold-start deploy race
  and the Jenkins-container `localhost`/network-namespace issue. Both were fixed with a
  retry loop and the `compose exec` healthcheck.
- Build **#6** was a transient Docker-socket permission failure after a container restart;
  it was removed after the Jenkins user was added to the root group, so the visible history
  reflects the validated pipeline. The fix is still in the running Jenkins container.

---

## 3. Videos

| File | Duration | Contents |
|------|----------|----------|
| `CivicLens-App-Walkthrough.mp4` | ~31 s | Home → scroll → map → marker popup → detail modal → report form (typed live) → About modal. Visible pointer and click ripples. |
| `CivicLens-Jenkins-Pipeline.mp4` | ~22 s | Job page → **Build Now** → build #10 in progress → console → **14 tests passed** → deploy/health → **Finished: SUCCESS**. |
| `CivicLens-Full-Demo.mp4` | ~60 s | Title card → app walkthrough → “Jenkins CI/CD Pipeline” card → full pipeline run → result card. Single presentation-ready file. |

All videos are **1600 × 1000, 30 fps, H.264/MP4, no audio**. The recordings are real
screen captures; the title cards in the full demo are the only generated frames.

---

## 4. Live endpoints (if demonstrating again)

| Service | URL / command | Notes |
|---------|---------------|-------|
| CivicLens app | `http://localhost:5000` | Docker container `civiclens-app`, healthcheck enabled |
| Health API | `http://localhost:5000/api/health` | Returns `{"service":"CivicLens","status":"ok",...}` |
| Jenkins | `http://localhost:8080` | No login (security disabled for the local lab) |
| Job | `http://localhost:8080/job/civiclens-pipeline/` | Pipeline from SCM, latest build #10 |
| Containers | `docker ps` | `jenkins` and `civiclens-app` |
| Rebuild | Jenkins → *Build Now* | Checkout → Install → Test → Docker Build → Deploy |

The app image is built and tagged per Jenkins build (`civiclens:<BUILD_NUMBER>` plus
`latest`); the pipeline redeploys with `docker compose` and verifies the health endpoint
from **inside** the app container. `docker-compose.yml` pins `image: civiclens:latest` and
`name: civiclens-pipeline`, so the running `civiclens-app` container always uses that single
image and the Compose stack never creates a second image or a duplicate data volume. Only
`civiclens:latest` is kept on the machine (older per-build tags are pruned); the base images
`python:3.11-slim` and `jenkins/jenkins:lts` stay because the build and Jenkins need them.
