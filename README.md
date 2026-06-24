# Ticket Analyzer

A minimal full-stack AI demo: a React/Vite frontend, a FastAPI backend,
a tiny Hugging Face sentiment model, and PostgreSQL — packaged as
multi-service Docker images and deployable locally, on the Poridhi
Cloud Lab VM, or on AWS EC2 via the **Puku CLI**.

See [`PRD.md`](./PRD.md) for the full product requirement document.

---

## Table of contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project layout](#project-layout)
- [Local setup](#local-setup)
- [Environment variables](#environment-variables)
- [API reference](#api-reference)
- [Deployment](#deployment)
  - [DockerHub images](#dockerhub-images)
  - [Poridhi Cloud VM](#poridhi-cloud-vm)
  - [AWS EC2 via Puku CLI](#aws-ec2-via-puku-cli)
- [Live URLs](#live-urls)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)

---

## Overview

**Ticket Analyzer** accepts a support ticket (title + message + optional
category), runs sentiment analysis on the message using a tiny
Hugging Face model (`distilbert-base-uncased-finetuned-sst-2-english`),
persists the result in PostgreSQL, and shows the ticket history in a
single-page React UI.

The stack demonstrates the full engineering path: PRD, frontend, backend,
AI model integration, database persistence, Docker images, DockerHub,
GitHub, and deployment on a Poridhi Lab VM / AWS EC2.

## Architecture

```
                ┌──────────────────────────┐
                │   Browser (User)         │
                │   http://<host>          │
                └────────────┬─────────────┘
                             │ HTTP
                             ▼
                ┌──────────────────────────┐
                │  Frontend (Nginx 1.27)   │
                │  Serves React SPA on :80 │
                │  Reverse-proxies /api →  │
                └────────────┬─────────────┘
                             │ /api/*  (internal Docker network)
                             ▼
                ┌──────────────────────────┐
                │  Backend (FastAPI)       │
                │  uvicorn on :8000        │
                │  - POST /tickets         │
                │  - GET  /tickets         │
                │  - GET  /health          │
                │  - Sentiment model       │
                │    (distilbert-sst-2)    │
                └────────────┬─────────────┘
                             │ SQLAlchemy
                             ▼
                ┌──────────────────────────┐
                │  PostgreSQL 16           │
                │  tickets table           │
                │  volume: pgdata          │
                └──────────────────────────┘
```

**Service-to-service flow:**

1. Browser loads the React SPA from the frontend container.
2. Browser calls `/api/...` (same origin) — the frontend container's
   Nginx reverse-proxies to the backend on the internal Docker network.
3. Backend runs the sentiment model in-process, persists the ticket,
   and returns the JSON.
4. No CORS is required because the browser only ever talks to one
   origin (the frontend).

## Project layout

```
ticket-analyzer/
├── PRD.md                          # Product requirement doc
├── README.md                       # ← you are here
├── docker-compose.yml              # Local dev (builds from sources)
├── .env.example                    # Template for .env (commit this)
├── .gitignore
├── backend/
│   ├── Dockerfile                  # CPU-only torch + model baked in
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app + routes
│       ├── config.py               # Strict env-var loader
│       ├── db.py                   # SQLAlchemy session
│       ├── models.py               # Ticket ORM
│       ├── schemas.py              # Pydantic request/response
│       └── sentiment.py            # HF model loader + analyzer
└── frontend/
    ├── Dockerfile                  # Vite build + Nginx serve
    ├── nginx.conf                  # Reverse proxy /api → backend
    ├── docker-entrypoint.sh        # envsubst template at runtime
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx                 # Form + ticket list UI
        └── styles.css              # Includes UNCERTAIN badge styles
```

## Local setup

### Prerequisites

- **Docker** 24+ and **Docker Compose** v2 (`docker compose version`)
- **Git**
- A DockerHub account (only required for image push / cloud deploy)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/CrimsonCompiler/Ticket-Analyzer.git
cd Ticket-Analyzer

# 2. Create the local environment file
cp .env.example .env
# (edit .env if you want — defaults work for local dev)

# 3. Build and start the stack
docker compose up --build
```

When the backend reports `Application startup complete.` and the
frontend Nginx is listening, open:

- **Frontend UI:** http://localhost:3000
- **Backend health (via frontend proxy):** http://localhost:3000/api/health
- **Backend direct (port 8000):** http://localhost:8000/health

The first backend start takes 30–60 seconds while the PyTorch runtime
warms up; subsequent requests are fast (the model is loaded once at
startup and kept in memory).

### Tear down

```bash
docker compose down              # stop + remove containers, keep DB volume
docker compose down -v           # also delete the pgdata volume (full reset)
```

## Environment variables

All configuration is driven by `.env` (gitignored). `docker compose`
reads it automatically. The backend **refuses to start** if any required
variable is missing — this is intentional so a misconfigured deployment
fails loudly.

| Variable | Required | Example | Purpose |
|---|---|---|---|
| `POSTGRES_USER` | yes | `postgres` | Postgres username |
| `POSTGRES_PASSWORD` | yes | `change-me-in-prod` | Postgres password |
| `POSTGRES_DB` | yes | `ticket_db` | Postgres database name |
| `DATABASE_URL` | yes | `postgresql://postgres:postgres@db:5432/ticket_db` | SQLAlchemy DSN |
| `MODEL_NAME` | yes | `distilbert-base-uncased-finetuned-sst-2-english` | Hugging Face model id |
| `HF_HOME` | yes | `/opt/hf-cache` | Where the model weights are baked |
| `TRANSFORMERS_OFFLINE` | yes | `1` | Force runtime to use the baked weights (no network) |
| `SENTIMENT_CONFIDENCE_THRESHOLD` | no | `0.80` | Below this, output is downgraded to `UNCERTAIN` |
| `VITE_API_BASE_URL` | yes | `/api` | Frontend build arg — same-origin path |
| `FRONTEND_PORT` | yes | `3000` | Host port mapped to Nginx (frontend) |
| `BACKEND_HOST` | yes | `backend` | Service name on the Docker network |
| `BACKEND_PORT` | yes | `8000` | Internal port uvicorn listens on |
| `DB_HOST` | yes | `db` | Postgres service name |
| `DB_PORT` | yes | `5432` | Postgres port |
| `DOCKERHUB_USERNAME` | yes | `tasrikk` | Used by the push script in the README |
| `IMAGE_TAG` | yes | `v1` | Tag used when building/pushing images |

## API reference

Base URL (local): `http://localhost:3000/api` (proxied) or
`http://localhost:8000` (direct).

### `GET /health`

Liveness probe. Returns `200 OK` whenever the backend process is up.

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:3000
```

**Response:**
```json
{ "status": "ok" }
```

### `POST /tickets`

Create a ticket, run sentiment analysis on the message, and persist it.

**Request:**
```http
POST /tickets HTTP/1.1
Host: localhost:3000
Content-Type: application/json

{
  "title": "Lab VM is down",
  "message": "The whole lab is unreachable and I have a deadline today, this is awful.",
  "category": "lab"
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `title` | string | yes | 1–255 chars |
| `message` | string | yes | non-empty |
| `category` | string | no | 1–64 chars |

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "Lab VM is down",
  "sentiment": "NEGATIVE",
  "confidence": 0.9987,
  "created_at": "2026-06-24T10:42:11.482310"
}
```

If the model's top-class confidence is below
`SENTIMENT_CONFIDENCE_THRESHOLD`, `sentiment` is set to `UNCERTAIN`
while `confidence` still reflects the raw score.

### `GET /tickets`

List tickets, newest first.

**Request:**
```http
GET /tickets HTTP/1.1
Host: localhost:3000
```

**Response:** `200 OK`
```json
[
  {
    "id": 2,
    "title": "Bug report",
    "sentiment": "NEGATIVE",
    "confidence": 0.99,
    "created_at": "2026-06-24T10:45:02.104221"
  },
  {
    "id": 1,
    "title": "Lab VM is down",
    "sentiment": "NEGATIVE",
    "confidence": 0.9987,
    "created_at": "2026-06-24T10:42:11.482310"
  }
]
```

## Deployment

### DockerHub images

Pre-built images live in DockerHub under the user namespace below.
The VM / EC2 compose files pull from these tags.

- Backend: [`tasrikk/ticket-analyzer-backend`](https://hub.docker.com/r/tasrikk/ticket-analyzer-backend) — `v1`
- Frontend: [`tasrikk/ticket-analyzer-frontend`](https://hub.docker.com/r/tasrikk/ticket-analyzer-frontend) — `v1`

To rebuild and push from your own laptop:

```bash
# PowerShell
$DHUB = "tasrikk"

docker build -t "$DHUB/ticket-analyzer-backend:v1" ./backend
docker build `
  --build-arg VITE_API_BASE_URL=/api `
  -t "$DHUB/ticket-analyzer-frontend:v1" `
  ./frontend

docker push "$DHUB/ticket-analyzer-backend:v1"
docker push "$DHUB/ticket-analyzer-frontend:v1"
```

> **Note:** PowerShell's automatic `$USER` variable collides with custom
> variables, so we use `$DHUB` here. On macOS/Linux, just use
> `docker build -t $DHUB/...` with a regular `export DHUB=...`.

### Poridhi Cloud VM

The Poridhi Lab hands-on terminal is a pre-provisioned VM. Deploy
straight from inside that terminal:

```bash
# 1. Log in to DockerHub
docker login

# 2. Bring up the project
mkdir -p ~/ticket-analyzer && cd ~/ticket-analyzer
git clone https://github.com/CrimsonCompiler/Ticket-Analyzer.git .

# 3. Point compose at the pushed images (the local `image:` tags are
#    replaced with your DockerHub tags; the `build:` sections are
#    simply ignored when only `image:` is set)
sed -i 's|ticket-analyzer-backend:local|tasrikk/ticket-analyzer-backend:v1|g' docker-compose.yml
sed -i 's|ticket-analyzer-frontend:local|tasrikk/ticket-analyzer-frontend:v1|g' docker-compose.yml

# 4. Start the stack
cp .env.example .env
docker compose pull
docker compose up -d
```

The frontend listens on port `3000` by default; if that port is in use
on the VM, edit `.env` and set `FRONTEND_PORT=8080` (or any free
port), then `docker compose up -d` again.

Verify:

```bash
docker compose ps
curl http://localhost:3000/api/health
# → {"status":"ok"}
```

### AWS EC2 via Puku CLI

The Puku CLI removes the need to click through the AWS console.

#### 1. One-time setup on your laptop

```bash
# Install Puku
irm https://puku.sh/install.ps1 | iex     # Windows / PowerShell
# (or) curl -fsSL https://puku.sh/install.sh | sh   # macOS/Linux

# Log in to Puku
puku auth login

# Add your AWS credentials (Access Key ID + Secret + region)
puku cloud configure --provider aws
```

The AWS keys can be created in **AWS Console → IAM → Users → Security
credentials → Create access key**. Use a user with at least
`AmazonEC2FullAccess` (or a tighter custom policy — see [Notes](#notes)).

#### 2. Launch an EC2 instance via Puku

```bash
puku compute create `
  --provider aws `
  --name ticket-analyzer-prod `
  --region ap-southeast-1 `
  --instance-type t3.small `
  --ami ubuntu-22.04
```

Puku auto-creates a security group (SSH + HTTP), provisions a key
pair, and returns a public IP.

#### 3. SSH into the instance

```bash
puku ssh ticket-analyzer-prod
```

#### 4. Install Docker and deploy

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Deploy
mkdir -p ~/ticket-analyzer && cd ~/ticket-analyzer
git clone https://github.com/CrimsonCompiler/Ticket-Analyzer.git .
cp .env.example .env

# Production-grade password
SECRET=$(openssl rand -base64 24 | tr -d '=+/' | cut -c1-24)
sed -i "s|POSTGRES_PASSWORD=postgres|POSTGRES_PASSWORD=$SECRET|" .env
sed -i "s|FRONTEND_PORT=3000|FRONTEND_PORT=80|" .env
sed -i "s|postgresql://postgres:postgres@|postgresql://postgres:$SECRET@|" .env

# Point compose at the pushed images
sed -i 's|ticket-analyzer-backend:local|tasrikk/ticket-analyzer-backend:v1|g' docker-compose.yml
sed -i 's|ticket-analyzer-frontend:local|tasrikk/ticket-analyzer-frontend:v1|g' docker-compose.yml

# Bring it up
docker login
docker compose pull
docker compose up -d
```

#### 5. Open the app

```bash
curl http://localhost/api/health
# → {"status":"ok"}
```

Visit `http://<EC2_PUBLIC_IP>` in a browser. The Puku output prints
the public IP after the `compute create` step.

#### 6. Tear down when done

```bash
puku compute delete ticket-analyzer-prod
```

Leaving an instance running incurs charges — always delete it once
the lab is over.

## Live URLs

| Resource | URL |
|---|---|
| GitHub repository | https://github.com/CrimsonCompiler/Ticket-Analyzer |
| DockerHub — backend image | https://hub.docker.com/r/tasrikk/ticket-analyzer-backend |
| DockerHub — frontend image | https://hub.docker.com/r/tasrikk/ticket-analyzer-frontend |
| Poridhi Lab deployment | (assigned by the Poridhi terminal — typically `http://<container-id>-3000.<region>.poridhi.dev`) |
| AWS EC2 deployment | (public IP printed by `puku compute create`) |

## Troubleshooting

### `pull access denied for ticket-analyzer-{backend,frontend}`

The local `docker-compose.yml` is still referencing the `image: ticket-analyzer-*:local`
tags that `docker compose` only knows about inside the original
laptop's local registry. On a fresh VM/EC2, those don't exist.

**Fix (on the VM/EC2):**

```bash
sed -i 's|ticket-analyzer-backend:local|tasrikk/ticket-analyzer-backend:v1|g' docker-compose.yml
sed -i 's|ticket-analyzer-frontend:local|tasrikk/ticket-analyzer-frontend:v1|g' docker-compose.yml
docker compose pull
```

### `failed to bind host port 0.0.0.0:3000`

Something else on the host is using port 3000.

**Fix:** Edit `.env` and pick a free port, e.g. `FRONTEND_PORT=8080`,
then `docker compose up -d` again.

### `VITE_API_BASE_URL is not set` at `vite build` time

`docker build` does **not** read `.env`; the build arg must be passed
explicitly. Either:

- Use the supplied `docker-compose.yml` (which passes
  `VITE_API_BASE_URL` from `.env` automatically), **or**
- Pass it manually: `docker build --build-arg VITE_API_BASE_URL=/api -t ...`

**Puku lesson learned:** in PowerShell, `$USER` is a built-in
automatic variable. Use a different name like `$DHUB` to avoid
silently expanding to your Windows login.

### `no resolver defined to resolve backend` (nginx)

Caused by using an nginx variable in `proxy_pass` (e.g.
`proxy_pass http://$backend_upstream/`) without a `resolver` directive.
This project avoids the issue by writing the upstream as a literal
`proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT}/;` and using
`envsubst` in the container entrypoint to substitute the real values
from the environment **before** nginx starts. nginx then sees a
literal host:port and skips the resolver code path entirely.

### `permission denied while trying to connect to the Docker daemon`

Add your user to the `docker` group and re-login:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Out-of-memory when the model loads

`distilbert-sst-2` plus PyTorch runtime needs ~1.5 GB of RAM. On
`t3.micro` (1 GB) the kernel may OOM-kill the backend. Use `t3.small`
(2 GB) or larger.

### `denied: requested access to the resource is denied` during push

DockerHub authentication failed. Re-run `docker login` and confirm
the username matches the namespace under which the repos live
(e.g. `tasrikk/...`).

## Notes

- The model weights are baked into the backend image at build time
  (`from_pretrained()`), and `TRANSFORMERS_OFFLINE=1` makes the
  container fail loudly if they're missing instead of silently
  downloading.
- The frontend Nginx reverse-proxies `/api` to the backend on the
  Docker network, so the same image works on `localhost`, on the
  Poridhi VM, and on AWS EC2 without rebuilding and without CORS.
- The backend runs `Base.metadata.create_all(engine)` on startup, so a
  fresh Postgres volume is ready immediately — no manual migrations.
- `distilbert-sst-2` is a binary classifier (POSITIVE/NEGATIVE). To
  avoid the model over-confidently labelling neutral text (release
  notes, how-to instructions, etc.) as one side or the other, we add a
  `SENTIMENT_CONFIDENCE_THRESHOLD` (default `0.80`). Outputs below
  the threshold are reported as `UNCERTAIN` with the raw confidence
  preserved so the UI can still show e.g. `UNCERTAIN (53.2%)`.
- The minimal IAM policy for a deployment-only user is roughly:

  ```json
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:DescribeInstances",
        "ec2:TerminateInstances",
        "ec2:CreateSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AllocateAddress",
        "ec2:AssociateAddress",
        "ec2:CreateKeyPair"
      ],
      "Resource": "*"
    }]
  }
  ```

  This is narrower than `AmazonEC2FullAccess` and is appropriate for
  short-lived lab deployments.
