# Mangrove Co-Pilot — Decision Tree Engine

A deterministic state-machine engine that drives Mangrove's resilience co-pilot
conversations. The engine routes a user through one of two decision trees —
**Redundancy** (Phases 1–6, Nodes 1–11) or **Dependency** (Nodes 1–4) — based
on the `Category` parameter passed in by the calling UI.

## Design philosophy

Per the project spec ("Glass Box, not Black Box"):

- **Branching is deterministic.** A Python state machine controls every
  transition. The LLM never decides which node comes next.
- **The LLM is a read-only voice layer.** It paraphrases facts retrieved from
  the Mangrove database and explains the journey in plain English. It cannot
  trigger a state transition.
- **External parameters drive the entry point.** When a user clicks "chat with
  co-pilot" on a survey, the UI hands the engine the `SurveyID`, `WorkspaceID`,
  and `Category`. The engine fetches the matching record and starts the right
  tree at the right station.

## Repository layout

```
mangrove_copilot/
├── __init__.py              # exports run_session()
├── models.py                # Pydantic payloads (TriggerPayload, SurveyData, …)
├── scoring.py               # calculate_resilience_score() — single source of truth
├── session.py               # top-level session orchestration
├── agent.py                 # Azure AI Foundry voice wrapper
├── console.py               # Console protocol + ScriptedConsole for tests
├── db/
│   ├── base.py              # MangroveRepo Protocol
│   ├── api_client.py        # real HTTP client → mangrove-api.azurewebsites.net
│   ├── stub.py              # in-memory fallback for offline / CI runs
│   └── factory.py           # picks repo impl based on env
├── engine/
│   ├── state_machine.py     # generic node-driven engine (max 50 hops safety guard)
│   ├── redundancy_tree.py   # Nodes 1–11 (full redundancy spec)
│   ├── dependency_tree.py   # Nodes 1–4 + 99 (dependency spec, with high/low paths)
│   └── router.py            # picks tree from Category
└── cli.py                   # local manual driver (python -m mangrove_copilot)
run_agent.py                 # Azure AI Foundry entry point
tests/                       # pytest suite (32 tests)
```

## Running locally

```powershell
pip install -r requirements.txt
python -m mangrove_copilot --survey-id survey-001 --workspace-id 12 --category Redundancy
```

With no `MANGROVE_API_BASE` env var set, the engine uses the in-memory stub
repo so you can drive every branch without credentials.

## Running tests

```powershell
pytest tests/ -v
```

## Foundry deployment

The `run_agent.py` entrypoint is what Azure AI Foundry executes when a
conversation starts. Foundry's "On Conversation Start" trigger should set the
following environment variables from the UI parameters:

| Env var          | Source (UI)                              | Required |
| ---------------- | ---------------------------------------- | -------- |
| `SURVEY_ID`      | active survey / entity row id            | yes      |
| `WORKSPACE_ID`   | active workspace                         | yes      |
| `CATEGORY`       | `Redundancy` or `Dependency`             | yes      |
| `USER_TOKEN`     | the user's JWT bearer token (per-session, forwarded by the frontend) | yes for live API |

Plus the platform secrets:

| Env var                       | Purpose                                     |
| ----------------------------- | ------------------------------------------- |
| `AZURE_AI_PROJECT_ENDPOINT`   | Foundry project endpoint                    |
| `FOUNDRY_AGENT_NAME`          | Registered agent name (e.g. `Decision-Tree-Redundancy`) |
| `FOUNDRY_AGENT_VERSION`       | Agent version pin                           |
| `MANGROVE_API_BASE`           | e.g. `https://mangrove-api.azurewebsites.net` |

### Why the user's JWT, not a service token

Mangrove's API enforces ownership through `[Authorize]` middleware that reads
the `id` claim out of the JWT. Forwarding the same token the user's browser
already holds means:

- The backend's existing `[Authorize]` checks naturally reject access to
  workspaces the user doesn't belong to.
- We don't introduce a new trust relationship or service principal.
- Tokens rotate automatically with the user's login session — no shared
  secret to manage.

The token never leaves the conversation: the engine forwards it on outbound
calls and discards it when the session ends.

## Adding a new tree

1. Drop a new module under `mangrove_copilot/engine/` that builds a list of
   `Node` objects.
2. Register it in `engine/router.py` against a new `Category` literal.
3. Extend `TriggerPayload.Category` in `models.py` with the new value.
4. Add a test under `tests/`.

## Known follow-ups

- Mangrove API authentication mode (bearer vs managed identity) needs to be
  confirmed with the API owner. The current client supports both.
- Owner picker (select from RACI stakeholders or workspace members) is
  implemented in the C# production backend but not yet ported to this engine.
- The scoring function lives here but the production backend reads a
  pre-calculated `resilience_score` from the DB — these should be reconciled.
