# Policy AI Agent

A **Python FastAPI** application that combines **organizations**, **users**, **leave requests**, **policies**, and an **AI chat assistant** powered by **Cohere** with **tool/function calling**. The AI answers questions using real data from the database and from **RAG (Retrieval-Augmented Generation)** over policy documents.

---

## What It Is

- **Policy & leave management**: Organizations have policies (e.g. leave, PTO, benefits). Users belong to organizations via memberships. Users can apply for leave per organization; admins can review and accept/reject.
- **AI Q&A assistant**: A chat endpoint where authenticated users ask questions. The AI uses **tools** to fetch organizations, policies, and policy document excerpts, then answers from that data—so responses are grounded in your app, not hallucinated.
- **RAG over policies**: Policy documents (PDF/DOCX or URLs) are chunked, embedded with Cohere, and stored. The assistant can search this index (optionally scoped to the user’s organizations) to answer policy questions from document content.

---

## How It Works

1. **Auth**: Most routes require JWT. User logs in at `/login` with username/password and gets a Bearer token.
2. **Data layer**: PostgreSQL (or SQLite for tests) stores users, organizations, user–organization memberships, policies, leave requests, and policy embeddings (pgvector).
3. **AI flow**:
   - User sends a question to `POST /ai_assistant` with the JWT.
   - The **PolicyAgent** gets the question plus the **current user’s ID**.
   - A **Cohere** chat model receives a system preamble, the question, and a list of **tools** (names + parameters).
   - The model may **call one or more tools** (e.g. “get my organization”, “search my organization’s policies”).
   - The app runs the corresponding functions (DB + RAG), returns results to the model.
   - The model uses tool results to write the final reply. Multiple tool-call rounds are allowed up to a step limit.
4. **User-scoped tools**: When `user_id` is present, the agent gets extra tools that use the request user’s identity (e.g. “my organization”, “policies for my org only”).

---

## AI Tools

The assistant can call these tools. Execution is done in your app; the model only chooses tools and parameters.

### Organization tools (`organizations/tools.py` + `organizations/db.py`)

| Tool | Description | Parameters |
|------|-------------|------------|
| **get_my_organization_details** | Returns the organization(s) the **requesting user** belongs to (via `UserOrganization`). Used for “tell me about my organization”, “my org details”, etc. | *(none)* |
| **get_organization_details** | Organization details by **name** (search). | `organization_name` |
| **get_policies_for_organization** | All policies for an organization by name. | `organization_name` |
| **get_policy_details** | Details of a specific policy by name. | `policy_name` |

### Policy search / RAG tools (`ai/tools.py` + `ai/rag.py`)

| Tool | Description | Parameters |
|------|-------------|------------|
| **search_my_organization_policies** | Semantic search over **policy document chunks** restricted to the **user’s organizations**. Used for “what is our leave policy?”, “how many sick days?”, etc. | `query`, `top_k` (optional) |
| **search_policy_embeddings** | Semantic search over **all** indexed policy chunks (no user filter). | `query`, `top_k` (optional) |

- **get_my_organization_details** and **search_my_organization_policies** are only available when the request is authenticated (user_id is set). Unauthenticated or missing user gets a subset of tools.

---

## RAG (Policy documents)

- **Indexing**: Policies can have documents (file upload or URL). Text is extracted (PDF/DOCX), chunked, embedded with Cohere, and stored in `policy_embeddings` (pgvector).
- **Query**: `RAGClient.query_policy_index(query, top_k, organization_ids=None)` embeds the query and returns the nearest chunks. If `organization_ids` is provided (e.g. the user’s orgs), only chunks from those organizations are considered.
- **Flow**: “Search my org policies” → resolve user’s org IDs from `UserOrganization` → call RAG with `organization_ids` → return excerpts to the model → model answers from that text.

---

## Main API Endpoints

### App & health
- `GET /` — Welcome and version
- `GET /health` — Health check
- `DELETE /admin/drop-db` — Drop all DB tables (use with care)

### Auth
- `POST /login` — Login with username/password; returns JWT (public)
- `POST /users` — Register (public)

### Users (authenticated)
- `GET /users` — List users (admin only)
- `GET /users/{user_id}` — Get user (self or admin)
- `GET /users/{user_id}/organizations` — Organizations the user belongs to
- `DELETE /users/{user_id}` — Delete user (admin)

### Organizations (authenticated)
- `GET /organizations` — List organizations
- `GET /organizations/{id}` — Get one
- `POST /organizations` — Create
- `PUT /organizations/{id}` — Update
- `DELETE /organizations/{id}` — Delete

### Policies (authenticated)
- `GET /policies` — List policies
- `GET /policies/{id}` — Get one
- `GET /organizations/{org_id}/policies` — Policies for an organization
- `POST /policies` — Create (with optional file upload)
- `PUT /policies/{id}` — Update
- `DELETE /policies/{id}` — Delete

### User–organization memberships (authenticated)
- `GET /user_organizations` — List memberships
- `GET /user_organizations/{id}` — Get one
- `GET /organizations/{org_id}/members` — Members of an organization
- `POST /user_organizations` — Add user to organization
- `PATCH /user_organizations/{id}` — Update (e.g. left_date, is_active)
- `DELETE /user_organizations/{id}` — Remove membership

### Leave requests (authenticated)
- `GET /leave_requests` — List (admin: all; user: own)
- `GET /leave_requests/{id}` — Get one
- `GET /organizations/{org_id}/leave_requests` — Leave requests for org (admin)
- `POST /leave_requests` — Apply for leave (user must be active member of org)
- `PATCH /leave_requests/{id}/review` — Accept/reject (admin)
- `DELETE /leave_requests/{id}` — Delete (owner or admin)

### AI
- `POST /ai_assistant` — Chat with the policy assistant (body: `question`, optional `session_id`). Uses JWT to get current user and enable user-scoped tools.
- `GET /ai/policy-embeddings` — List policy embedding rows (e.g. for debugging; optional filters).

---

## Folder structure

```
PolicyAgent/
├── application/     # FastAPI app, CORS, auth middleware, route imports
├── auth/            # JWT create/decode, password hash, login, require_authenticated_user
├── database/        # DB engine, SessionLocal, init_db, drop_db
├── users/           # User model, APIs (users + leave_requests), utils
├── organizations/   # Organization, Policy, UserOrganization models & APIs
│                    # + tools (AI tool definitions) + db (get_org_details, get_my_org, etc.)
├── ai/              # PolicyAgent, Cohere client, tool-call loop
│                    # tools (search_my_organization_policies, search_policy_embeddings)
│                    # rag (RAGClient: index + query_policy_index), prompts, apis
├── main.py          # Run uvicorn
└── tests/           # Pytest (conftest, test_* for app, auth, users, orgs, leave, AI)
```

---

## Setup

1. **Clone** the repository.

2. **Environment**  
   Add a `.env` (or export variables). Required:
   - `DATABASE_URL` — or `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`
   - `JWT_SECRET`
   - `COHERE_API_KEY`
   - `COHERE_LLM_MODEL` (e.g. `command-a-03-2025`)

   Optional:
   - `JWT_ALGORITHM` (default `HS256`), `JWT_EXPIRE_MINUTES` (default `60`)
   - `API_PORT` (default `8000`)
   - `COHERE_EMBED_MODEL` (default `embed-english-v3.0`) for RAG
   - `AI_AGENT_MAX_STEPS`, `POLICY_RAG_TOP_K`, `RAG_EMBED_DIM` for agent/RAG tuning

3. **Install**  
   `pip install -r requirements.txt`

4. **Run**  
   `python main.py`  
   Or: `make start` (if Makefile exists).  
   API: `http://localhost:8000`  
   Docs: `http://localhost:8000/docs`

---

## Example `.env`

```env
API_PORT=8000
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=policyagent
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
COHERE_API_KEY=your-cohere-key
COHERE_LLM_MODEL=command-a-03-2025
JWT_SECRET=your-strong-secret
```

---

## Build & test

- **Build**: `make build` (if configured)
- **Tests**: `make test` or `pytest tests/ -v`

Tests use an in-memory SQLite DB by default (`TEST_DATABASE_URL` can override). They cover users (create, duplicate validation 409, 404), auth (login, 401), organizations and memberships, leave requests, AI agent (user_id wiring, DummyClient/Spy), and organization DB helpers (`get_my_organization_details`, `get_organization_ids_for_user`).

---

## Summary

- **Policy AI Agent API** = FastAPI + JWT + Organizations/Users/Policies/Leave requests + Cohere chat with **tool calling** and **RAG** over policy documents.
- **Tools** = organization lookup (by name + “my organization”), policy list/details, and two search tools: one scoped to the user’s orgs, one global.
- **Flow** = user asks in natural language → model picks tools → app runs them (DB + optional RAG) → model answers from results. User-scoped tools only when the request is authenticated and `user_id` is passed into the agent.
