"""
Test node parameters functionality for backend simulation.
Run with: python test_node_params.py
Ensure backend is running: cd backend && uvicorn app.main:app --reload
"""
import requests
import json

BASE = "http://localhost:8000"

def test_simulation_with_node_params():
    """Test simulation with custom node parameters."""
    print("\n" + "="*60)
    print("Testing Simulation with Node Parameters")
    print("="*60 + "\n")
    
    # Test 1: Basic simulation without node parameters (default behavior)
    print("Test 1: Basic simulation (no node params)")
    print("-" * 60)
    payload_basic = {
        "num_banks": 5,
        "num_steps": 10,
        "use_featherless": False,
        "verbose": False,
        "lending_amount": 10.0,
        "investment_amount": 10.0,
        "connection_density": 0.2
    }
    
    try:
        r = requests.post(f"{BASE}/api/simulation/run", json=payload_basic, timeout=30)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"✓ Success! Summary: {json.dumps(data['summary'], indent=2)}")
        else:
            print(f"✗ Failed: {r.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Simulation with custom node parameters
    print("\n" + "-" * 60)
    print("Test 2: Simulation with custom node parameters")
    print("-" * 60)
    
    node_params = [
        {
            "node_id": "bank1",
            "initial_capital": 200.0,
            "initial_liquidity": 100.0,
            "risk_level": 0.1,
            "strategy": "conservative",
            "lending_amount": 15.0,
            "investment_amount": 5.0
        },
        {
            "node_id": "bank2",
            "initial_capital": 150.0,
            "initial_liquidity": 75.0,
            "risk_level": 0.3,
            "strategy": "balanced",
            "lending_amount": 10.0,
            "investment_amount": 10.0
        },
        {
            "node_id": "bank3",
            "initial_capital": 100.0,
            "initial_liquidity": 40.0,
            "risk_level": 0.5,
            "strategy": "aggressive",
            "lending_amount": 5.0,
            "investment_amount": 20.0
        }
    ]
    
    payload_custom = {
        "num_banks": 3,  # Will be overridden by length of node_parameters
        "num_steps": 10,
        "use_featherless": False,
        "verbose": False,
        "lending_amount": 10.0,  # Default, but overridden by node params
        "investment_amount": 10.0,  # Default, but overridden by node params
        "connection_density": 0.3,
        "node_parameters": node_params
    }
    
    try:
        r = requests.post(f"{BASE}/api/simulation/run", json=payload_custom, timeout=30)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"✓ Success with custom node params!")
            print(f"Summary: {json.dumps(data['summary'], indent=2)}")
            print(f"\nNode parameters used:")
            for i, node in enumerate(node_params):
                print(f"  Bank {i}: {node['strategy']} strategy, "
                      f"capital={node['initial_capital']}, "
                      f"liquidity={node['initial_liquidity']}, "
                      f"risk={node['risk_level']}")
        else:
            print(f"✗ Failed: {r.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Mixed scenario - some custom params, more banks than params
    print("\n" + "-" * 60)
    print("Test 3: Mixed scenario (5 banks, 2 custom params)")
    print("-" * 60)
    
    partial_node_params = [
        {
            "node_id": "special_bank_1",
            "initial_capital": 300.0,
            "initial_liquidity": 150.0,
            "risk_level": 0.05,
            "strategy": "conservative",
            "lending_amount": 20.0,
            "investment_amount": 5.0
        },
        {
            "node_id": "special_bank_2",
            "initial_capital": 80.0,
            "initial_liquidity": 30.0,
            "risk_level": 0.6,
            "strategy": "aggressive",
            "lending_amount": 5.0,
            "investment_amount": 25.0
        }
    ]
    
    payload_mixed = {
        "num_banks": 5,
        "num_steps": 10,
        "use_featherless": False,
        "verbose": False,
        "lending_amount": 10.0,
        "investment_amount": 10.0,
        "connection_density": 0.2,
        "node_parameters": partial_node_params
    }
    
    try:
        r = requests.post(f"{BASE}/api/simulation/run", json=payload_mixed, timeout=30)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"✓ Success with partial custom params!")
            print(f"Summary: {json.dumps(data['summary'], indent=2)}")
            print(f"\nNote: First 2 banks use custom params, remaining 3 use defaults")
        else:
            print(f"✗ Failed: {r.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("\nNode Parameters API Test")
    print("Making sure backend is accessible at", BASE)
    
    try:
        r = requests.get(f"{BASE}/health", timeout=5)
        if r.status_code == 200:
            print("✓ Backend is running!")
            test_simulation_with_node_params()
        else:
            print("✗ Backend returned non-200 status")
    except Exception as e:
        print(f"✗ Cannot connect to backend: {e}")
        print("\nPlease ensure backend is running:")
        print("  cd backend && uvicorn app.main:app --reload")
