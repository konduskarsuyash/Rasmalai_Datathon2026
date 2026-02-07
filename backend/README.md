# Financial Network Backend API

MVP backend for **Network-Based Game-Theoretic Modeling of Financial Infrastructure**.

## Setup

From project root (`Rasmalai_Datathon2026`):

```bash
cd Rasmalai_Datathon2026
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r backend/requirements.txt
```

## Run

From **backend** directory (project root is auto-added to path for `core_implementation`):

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or from project root with module path:

```bash
cd Rasmalai_Datathon2026
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

## Endpoints

| Feature | Endpoints |
|---------|-----------|
| **Networks** | `POST /api/networks/`, `GET /api/networks/`, `GET /api/networks/{id}`, `GET /api/networks/{id}/metrics`, `DELETE /api/networks/{id}` |
| **Contagion** | `POST /api/contagion/simulate`, `POST /api/contagion/stress-test` |
| **Equilibrium** | `POST /api/equilibrium/compute` |

Networks are stored in memory (no DB). Create a network with `POST /api/networks/` then use its `id` in contagion and equilibrium requests.
