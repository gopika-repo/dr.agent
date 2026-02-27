# Docker Deployment for Competition Analyser

This project supports containerized deployment using Docker.

## Prerequisites
- Docker and Docker Compose installed.
- A `.env` file based on `.env.example` with your API keys.

## Quick Start (Docker Compose)
To start both the FastAPI backend and the Streamlit UI:

```bash
docker-compose up --build
```

- **FastAPI API**: [http://localhost:8000](http://localhost:8000)
- **Streamlit UI**: [http://localhost:8501](http://localhost:8501)

## Using the Dockerfile Directly
To build only the API container:

```bash
docker build -t competition-analyser-api .
docker run -p 8000:8000 --env-file .env competition-analyser-api
```

## Notes
- The `Dockerfile` is optimized for production with a multi-stage approach (optional) and a non-root user.
- `init_db` or any first-run scripts should be handled via the environment or entrypoint if necessary.
