## AI‑Powered Restaurant Recommendation System

Phase 0 sets up the project foundations (config, env handling, logging, error handling) and a runnable skeleton server.

### What’s included (Phase 0)

- **Basic web UI** as the initial input source (served as static files: `index.html`, `styles.css`, `script.js`)
- **Environment variable loading** via `.env`
- **Structured JSON logging** (requests + crashes)
- **Centralized error handling**
- **Health check** endpoint at `/health`

### Requirements

- Node.js 18+ (recommended)

### Setup

1. Create a local environment file:

```bash
cp .env.example .env
```

2. Start the server:

```bash
node src/server.js
```

### Verify

- Open `http://localhost:3000` to see the current UI.
- Open `http://localhost:3000/health` to verify the server is running.

