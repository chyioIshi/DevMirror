# DevMirror

DevMirror is a mock service platform inspired by WireMock. It lets you define HTTP mocks, match incoming requests dynamically, and return configured responses from a FastAPI service backed by MongoDB.

## Features

- HTTP mock handling through a catch-all FastAPI route
- Dynamic request matching by headers, query parameters, request path, and JSON body fields
- Configurable response status, headers, and body
- Scoped mocks for separating mock behavior by request context
- Mock activation and conflict checks
- Request logging and request log verification endpoints
- Admin endpoints for creating, updating, listing, activating, and deleting mocks
- MongoDB persistence with Beanie
- Optional async side effect execution through Celery and Redis
- Async-first application flow

## Tech Stack

- Python 3.13+
- FastAPI
- MongoDB
- Beanie
- Pydantic
- AsyncIO
- Celery
- Redis
- Uvicorn
- Ruff

## Architecture

DevMirror follows Clean Architecture-inspired boundaries without trying to be overly formal.

- `domain` contains core models, policies, and business rules.
- `application` contains use cases, commands, mappers, and services.
- `infra` contains MongoDB, logging, request parsing, and response-building details.
- `api` contains FastAPI routes, contracts, middleware, and error handlers.

## Project Structure

```text
app/
  api/             FastAPI routes, contracts, middleware
  application/     use cases, commands, services, mappers
  domain/          domain models, policies, repository ports
  infra/           MongoDB, logging, request/response infrastructure
  di/              dependency wiring
  main.py          FastAPI application factory
```

## Getting Started

Clone the repository:

```bash
git clone https://github.com/chyioIshi/DevMirror.git
cd DevMirror
```

Create a virtual environment:

```bash
uv venv
```

Activate it:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install uv
uv sync
```

Start MongoDB:

```bash
docker compose up -d mongo
```

Start the app:

```bash
uv run uvicorn app.main:app --reload
```

The service should be available at:

```text
http://localhost:8000
```

API docs are available at:

```text
http://localhost:8000/docs
```

## Environment Variables

DevMirror reads configuration from environment variables or a local `.env` file.

```env
MONGO_DSN=mongodb://localhost:27017
MONGO_DATABASE=devmirror
LOG_LEVEL=INFO
ASYNC_TASK_SCHEDULER=in_process
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_TASK_QUEUE=side_effects.default
CELERY_TASK_ACKS_LATE=true
CELERY_TASK_REJECT_ON_WORKER_LOST=true
# CELERY_TASK_TIME_LIMIT=30
# CELERY_TASK_SOFT_TIME_LIMIT=25
```

Useful defaults are defined in `app/config.py`.

## Running the Service

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Running With Celery Side Effects

Async side effects can run through Celery with Redis as the broker. The API process still only calls the application `AsyncTaskScheduler` port; Celery is wired in infrastructure.

Start MongoDB, Redis, the API, and the worker:

```bash
docker compose up --build app celery-worker
```

For local development without Docker Compose, start Redis and run:

```bash
set ASYNC_TASK_SCHEDULER=celery
set CELERY_BROKER_URL=redis://localhost:6379/1
set CELERY_TASK_QUEUE=side_effects.default
uv run uvicorn app.main:app --reload
```

In another shell:

```bash
uv run celery -A app.infra.celery.app:celery_app worker --loglevel=info -Q side_effects.default,side_effects.kafka,side_effects.http,side_effects.db
```

The Celery scheduler always publishes async side effect tasks to the broker. Use
the in-process scheduler for unit tests that should avoid Redis and a worker.
Parallel async side effects are fan-out tasks routed by side effect type. Sequential
async side effects are sent as one ordered batch task and executed by the dispatcher.

Async side effects use Celery's at-least-once delivery model. Providers should be
written so repeated execution with the same request context is acceptable.
`fail_policy=fail_mock` is only supported for `mode=sync`, because async side
effects run after the HTTP response has already been returned.

## Example API Usage

Create a mock:

```bash
curl -X POST http://localhost:8000/admin/mocks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get-user-profile",
    "description": "Mock profile response for local development",
    "path": "/api/users/42",
    "method": "GET",
    "priority": 10,
    "scope": "global",
    "match_rules": [
      {
        "source": "header",
        "key": "x-test-user",
        "operator": "eq",
        "expected": "test-user"
      }
    ],
    "response": {
      "status_code": 200,
      "headers": {
        "Content-Type": "application/json"
      },
      "body": {
        "id": 42,
        "name": "test_user",
        "role": "tester"
      }
    },
    "tags": ["users", "test"]
  }'
```

New mocks are created inactive. Activate the mock using the returned `id`:

```bash
curl -X POST "http://localhost:8000/admin/mocks/<mock-id>/activate"
```

Call the mocked endpoint:

```bash
curl http://localhost:8000/api/users/42 \
  -H "x-test-user: test-user"
```

Sample response:

```json
{
  "id": 42,
  "name": "test_user",
  "role": "tester"
}
```

## Current Status

DevMirror is actively developed. APIs, contracts, and internal structure may still change as the implementation evolves.

Planned areas include scenarios, side-effect handling, and plugin-style extension points.

## License

MIT
