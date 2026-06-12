# DevMirror

[![Coverage Status](https://coveralls.io/repos/github/chyioIshi/DevMirror/badge.svg?branch=main)](https://coveralls.io/github/chyioIshi/DevMirror?branch=main)
[![CI](https://github.com/chyioIshi/DevMirror/actions/workflows/ci.yml/badge.svg)](https://github.com/chyioIshi/DevMirror/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async%20API-green)
![MongoDB](https://img.shields.io/badge/MongoDB-Beanie-green)
![Code style](https://img.shields.io/badge/code%20style-ruff-black)
![Tests](https://img.shields.io/badge/tests-pytest-blue)
![License](https://img.shields.io/github/license/chyioIshi/DevMirror)

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
- Async-first application flow

## Tech Stack

- Python 3.13+
- FastAPI
- MongoDB
- Beanie
- Pydantic
- AsyncIO
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
