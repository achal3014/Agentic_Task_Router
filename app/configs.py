import configparser

config = configparser.ConfigParser()
config.read("configs.ini")

MAIN_MODEL = config["LLM"]["MAIN_MODEL"]
FALLBACK_MODEL = config["LLM"]["FALLBACK_MODEL"]
ROUTER_MODEL = config["LLM"]["ROUTER_MODEL"]
MAX_TOKENS = int(config["LLM"]["MAX_TOKENS"])
TEMPERATURE = float(config["LLM"]["TEMPERATURE"])

ENABLE_TIER2 = config["SAFETY"].getboolean("ENABLE_TIER2")

ENABLE_LOGGING = config["LOGGING"].getboolean("ENABLE_LOGGING")
