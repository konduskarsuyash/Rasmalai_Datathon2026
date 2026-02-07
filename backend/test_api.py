"""
Quick API tests. Run with: python test_api.py
Ensure backend is running: cd backend && uvicorn app.main:app --reload
"""
import requests

BASE = "http://localhost:8000"

def test(name, method, url, **kwargs):
    try:
        r = requests.request(method, url, timeout=10, **kwargs)
        print(f"{name}: {r.status_code} {r.json() if r.headers.get('content-type', '').startswith('application/json') else r.text[:80]}")
        return r
    except Exception as e:
        print(f"{name}: ERROR {e}")
        return None

if __name__ == "__main__":
    print("Testing API at", BASE)
    print("-" * 50)
    test("GET /", "GET", f"{BASE}/")
    test("GET /health", "GET", f"{BASE}/health")
    test("GET /api/me", "GET", f"{BASE}/api/me")
    test("GET /api/config/", "GET", f"{BASE}/api/config/")
    test("POST /api/networks/ (create)", "POST", f"{BASE}/api/networks/", json={"name": "Test Network", "num_banks": 5})
    r = test("POST /api/simulation/run", "POST", f"{BASE}/api/simulation/run", json={"num_banks": 5, "num_steps": 3, "verbose": False})
    if r and r.status_code == 200:
        d = r.json()
        print("  -> summary:", d.get("summary", {}))
    print("-" * 50)
    print("Done. Open http://localhost:8000/docs for Swagger UI.")
