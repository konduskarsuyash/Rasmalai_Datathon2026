"""Test imports for new node parameters functionality."""
try:
    from app.core import BankConfig, SimulationConfig
    print("[OK] BankConfig imported successfully")
    print("[OK] SimulationConfig imported successfully")
    
    from app.schemas.simulation import NodeParameters, SimulationRunRequest
    print("[OK] NodeParameters imported successfully")
    print("[OK] SimulationRunRequest imported successfully")
    
    # Test instantiation
    bank_config = BankConfig(
        initial_capital=100.0,
        initial_liquidity=50.0,
        risk_level=0.2,
        strategy="balanced"
    )
    print(f"[OK] BankConfig instance created: {bank_config}")
    
    node_params = NodeParameters(
        node_id="test_bank",
        initial_capital=100.0,
        initial_liquidity=50.0,
        risk_level=0.2,
        strategy="balanced"
    )
    print(f"[OK] NodeParameters instance created: {node_params}")
    
    print("\n[SUCCESS] All imports and instantiations successful!")
    
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
