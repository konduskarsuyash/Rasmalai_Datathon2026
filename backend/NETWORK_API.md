# Create network API (wireframe)

## Endpoint

- **Create:** `POST /api/networks/`
- **List:** `GET /api/networks/`
- **Get one:** `GET /api/networks/{network_id}`

## Basic payload to create a single network

Minimal (all optional fields use defaults):

```json
{
  "name": "My First Network"
}
```

With all fields:

```json
{
  "name": "EU Banking Network",
  "num_banks": 20,
  "connection_density": 0.2,
  "description": "Sample interbank network for EU stress test"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | — | Network name (1–200 chars) |
| `num_banks` | int | No | 20 | Number of banks (1–100) |
| `connection_density` | float | No | 0.2 | Interbank link density 0–1 |
| `description` | string | No | null | Optional description (max 500 chars) |

## Example response (201)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "EU Banking Network",
  "num_banks": 20,
  "connection_density": 0.2,
  "description": "Sample interbank network for EU stress test",
  "status": "created"
}
```

Use `id` to fetch the network later (`GET /api/networks/{id}`) or to run simulations keyed by network (when wired up).

## cURL example

```bash
curl -X POST http://localhost:8000/api/networks/ \
  -H "Content-Type: application/json" \
  -d '{"name": "My First Network", "num_banks": 10}'
```
