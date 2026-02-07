"""
Configuration settings for the Financial Network MVP.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Network Configuration
NUM_AGENTS = 40
TIME_STEPS = 30

# Agent Defaults
DEFAULT_CAPITAL = 100.0
DEFAULT_LIQUIDITY = 50.0
DEFAULT_THRESHOLD = 20.0  # Below this capital, agent defaults

# Featherless.ai Configuration
FEATHERLESS_AGENT_RATIO = 0.25  # 25% of agents use LLM for decisions
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY", "")
FEATHERLESS_BASE_URL = "https://api.featherless.ai/v1"
FEATHERLESS_MODEL = "deepseek-ai/DeepSeek-V3.2"

# Risk Parameters
RISK_NOISE_STD = 0.1
MIN_EXPOSURE = 5.0
MAX_EXPOSURE = 20.0

# Shock Configuration
SHOCK_MAGNITUDE = 50.0
SHOCK_PROBABILITY = 0.1  # Per time step

# Logging
VERBOSE = True
