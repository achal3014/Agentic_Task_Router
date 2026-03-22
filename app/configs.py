import configparser

config = configparser.ConfigParser()
config.read("configs.ini")

# ─────────────────────────────────────────────
# LLM
# ─────────────────────────────────────────────
MAIN_MODEL = config["LLM"]["MAIN_MODEL"]
MAX_TOKENS = int(config["LLM"]["MAX_TOKENS"])
TEMPERATURE = float(config["LLM"]["TEMPERATURE"])
FALLBACK_MODEL = config["LLM"]["FALLBACK_MODEL"]
ROUTER_MODEL = config["LLM"]["ROUTER_MODEL"]
ROUTER_TEMPERATURE = float(config["LLM"]["ROUTER_TEMPERATURE"])
ROUTER_MAX_TOKENS = int(config["LLM"]["ROUTER_MAX_TOKENS"])
RESEARCH_TEMPERATURE = float(config["LLM"]["RESEARCH_TEMPERATURE"])
RESEARCH_MAX_TOKENS = int(config["LLM"]["RESEARCH_MAX_TOKENS"])
TOOL_USE_MODEL = config["LLM"]["TOOL_USE_MODEL"]

# ─────────────────────────────────────────────
# Safety
# ─────────────────────────────────────────────
ENABLE_TIER2 = config["SAFETY"].getboolean("ENABLE_TIER2")

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
ENABLE_LOGGING = config["LOGGING"].getboolean("ENABLE_LOGGING")

# ─────────────────────────────────────────────
# Memory
# ─────────────────────────────────────────────
EMBEDDING_MODEL = config["MEMORY"]["EMBEDDING_MODEL"]
ENABLE_MEMORY = config["MEMORY"].getboolean("ENABLE_MEMORY")
REDIS_HOST = config["MEMORY"]["REDIS_HOST"]
REDIS_PORT = int(config["MEMORY"]["REDIS_PORT"])
REDIS_TTL_SECONDS = int(config["MEMORY"]["REDIS_TTL_SECONDS"])
VECTOR_STORE_PATH = config["MEMORY"]["VECTOR_STORE_PATH"]
HISTORY_TURNS = int(config["MEMORY"]["HISTORY_TURNS"])

# ─────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────
ENABLE_WEB_SEARCH = config["TOOLS"].getboolean("ENABLE_WEB_SEARCH")

# ─────────────────────────────────────────────
# Cost
# ─────────────────────────────────────────────
COST_PER_1K_TOKENS_MAIN = float(config["COST"]["COST_PER_1K_TOKENS_MAIN"])
COST_PER_1K_TOKENS_FALLBACK = float(config["COST"]["COST_PER_1K_TOKENS_FALLBACK"])
COST_PER_1K_TOKENS_ROUTER = float(config["COST"]["COST_PER_1K_TOKENS_ROUTER"])

# ─────────────────────────────────────────────
# Routing
# ─────────────────────────────────────────────
MIN_CONFIDENCE_THRESHOLD = float(config["ROUTING"]["MIN_CONFIDENCE_THRESHOLD"])
