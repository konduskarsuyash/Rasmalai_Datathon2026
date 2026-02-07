# Financial Network Backend API

**Auth + simulation logic.** All logic lives inside `backend/app`:

- **`app/config/`** – `settings.py` (NUM_AGENTS, TIME_STEPS, FEATHERLESS_*, etc.)
- **`app/core/`** – v2: `transaction`, `balance_sheet`, `bank`, `market`, `simulation_v2`
- **`app/ml/`** – `policy.py` (select_action for simulation v2)
- **`app/featherless/`** – optional `decision_engine` (strategic priority when API key set)

## Setup

From project root (`Rasmalai_Datathon2026`):

```bash
pip install -r backend/requirements.txt
```

Set in `.env` or `backend/.env`:

- **Auth:** `CLERK_SECRET_KEY`, optional `CLERK_API_URL`
- **Featherless (optional):** `FEATHERLESS_API_KEY` to enable LLM priority in simulation

## Run

From project root:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Or from backend directory:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

## Endpoints

| Feature | Endpoint |
|--------|----------|
| Root | `GET /` – service info |
| Health | `GET /health` – status |
| Auth | `GET /api/me` – current user (Clerk) |
| Config | `GET /api/config/` – public config (no secrets) |
| Simulation | `POST /api/simulation/run` – run v2 simulation (body: `num_banks`, `num_steps`, `use_featherless`, `verbose`, etc.) |

### POST /api/simulation/run

Request body (all optional):

- `num_banks` (default 20)
- `num_steps` (default 30)
- `use_featherless` (default false) – use Featherless for priority when API key set
- `verbose` (default false) – include `bank_logs` in response
- `lending_amount`, `investment_amount`

Returns: `summary`, `defaults_over_time`, `total_equity_over_time`, `market_prices`, `cascade_events`, `system_logs`, optional `bank_logs`.
