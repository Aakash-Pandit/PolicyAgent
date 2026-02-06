# Project Overview

Suggested name: **Leave Query AI Agent**

This project is a Python-based leave query system that combines standard
CRUD flows for leave requests/appointments with an AI-driven Q&A assistant 
to help users understand and manage scheduling. It can be described as a 
lightweight AI agent (tool-calling) app.

## Key Concepts

- **Appointments/Leaves**: Records that store scheduling details including title, date/time, and status.
- **AI Q&A**: A lightweight interface for answering questions about the system,
  helping users navigate or understand scheduling rules.
- **LLM tool calling**: The AI uses a Cohere language model with tool/function
  calling to fetch and manage leave/appointment data as needed.

## What It Does

- Provides APIs for creating and managing leave requests/appointments.
- Persists data through a database layer.
- Exposes an AI Q&A route to respond to user questions about leaves and
  project usage.
- Secures most routes with JWT auth (login + bearer token).

## AI Concept Used

The project is based on **LLM tool/function calling**. Instead of the AI
hallucinating answers, it chooses from a set of predefined tools (functions)
that read real data from the system. The workflow is:

1. The LLM receives a user question plus a system preamble.
2. It selects one or more tools and passes structured parameters.
3. The app runs those tools against the database.
4. The LLM uses the tool results to compose the final response.

This makes the AI **grounded** in live application data and reduces incorrect
answers.

## AI Classification

- **AI Agent (tool-calling)**: The model selects tools, the app executes them,
  and the model composes the final answer from results.
- **Lightweight agentic flow**: It is a single-step decision with tools, not a
  multi-step planner or autonomous agent loop.

## How It Works

1. **Application entrypoint** initializes the server and routes.
2. **Appointments module** handles leave/appointment database logic and API endpoints.
3. **AI module** (`ai/clients.py`, `ai/apis.py`) uses a Cohere LLM with tool
   calling to select database functions, then composes a final answer from the
   tool results.
4. **Database layer** manages storage and retrieval.

## Typical Flow

1. Create a leave request with a title and schedule time.
2. Query or update leave status.
3. Ask AI questions about leaves, availability, or usage.

## Folder Structure (High Level)

- `application/`: App setup and routing.
- `appointments/`: Leave/appointment models, APIs, and DB logic.
- `ai/`: AI Q&A logic.
- `database/`: Shared database utilities.
- `auth/`: JWT authentication.
- `users/`: User management.

## Setup

1. Clone the repository.
2. After cloning, add a `.env` file and set the required environment variables
   for your environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `python main.py`

## Environment Variables

Required (production):
- `DATABASE_URL` (or `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`,
  `POSTGRES_PORT`, `POSTGRES_DB`)
- `JWT_SECRET`
- `COHERE_API_KEY`
- `COHERE_LLM_MODEL`

Optional:
- `JWT_ALGORITHM` (default: `HS256`)
- `JWT_EXPIRE_MINUTES` (default: `60`)
- `API_PORT` (default: `8000`)

## Sample `.env`

```env
PYTHONDONTWRITEBYTECODE=1
API_PORT=8000
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=leavequery
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
COHERE_API_KEY=replace-with-cohere-key
COHERE_LLM_MODEL=command-a-03-2025
JWT_SECRET=replace-with-strong-secret
```

## Build

To build project: `make build`

## Start

To start project: `make start`

## Tests

Run all tests: `make test`
