# Ticket Analyzer

A minimal full-stack AI demo: React/Vite frontend, FastAPI backend, tiny
Hugging Face sentiment model, and PostgreSQL — all runnable locally and
on a Poridhi Lab VM via Docker Compose.

See `PRD.md` for the full product requirement document.

## Project layout

```
ticket-analyzer/
├── PRD.md
├── README.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   └── app/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    └── src/
```

## Run locally

```bash
docker compose up --build
```

Then open http://localhost:3000.

- Frontend: http://localhost:3000
- Backend health: http://localhost:3000/api/health
- Backend direct: http://localhost:8000/health

## Run on the Poridhi Lab VM

1. Build and push images to DockerHub from your laptop:

   ```bash
   docker build -t <dockerhub-username>/ticket-analyzer-backend:v1 ./backend
   docker build -t <dockerhub-username>/ticket-analyzer-frontend:v1 ./frontend

   docker push <dockerhub-username>/ticket-analyzer-backend:v1
   docker push <dockerhub-username>/ticket-analyzer-frontend:v1
   ```

2. On the VM, copy the same `docker-compose.yml` from this repo
   (no `build:` sections — just swap the `image:` lines to your
   pushed tags). All secrets still come from the VM's `.env` file
   (copy from `.env.example` and fill in real values).

3. Start the stack on the VM:

   ```bash
   docker compose up -d
   ```

   Visit the VM's port 3000 in a browser.

## API

- `GET  /health`  — returns `{"status":"ok"}`
- `POST /tickets` — body: `{"title","message","category?"}` → creates a
  ticket, runs sentiment, saves it, returns the full record.
- `GET  /tickets` — lists saved tickets (newest first).

## Notes

- The model weights are baked into the backend image at build time
  (`from_pretrained()`), and `TRANSFORMERS_OFFLINE=1` makes the
  container fail loudly if they're missing instead of silently
  downloading.
- The frontend Nginx reverse-proxies `/api` to the backend on the
  Docker network, so the same image works on `localhost` and on the
  Poridhi Lab VM without rebuilding and without CORS.
- The backend runs `Base.metadata.create_all(engine)` on startup, so a
  fresh Postgres volume is ready immediately — no manual migrations.
