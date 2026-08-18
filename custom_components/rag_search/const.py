"""Constants for the RAG Search integration."""

DOMAIN = "rag_search"

# Services
SERVICE_SEARCH_HISTORY = "search_history"

# Configuration keys
CONF_OPENAI_API_KEY = "openai_api_key"
CONF_OPENAI_MODEL = "openai_model"
CONF_ENTITY_SCOPE = "entity_scope"
CONF_MAX_ITEMS = "max_items"

# Defaults
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_ITEMS = 50

# OpenAI API
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODELS_URL = "https://api.openai.com/v1/models"
OPENAI_MAX_TOKENS = 150

# Networking behaviour for the raw aiohttp OpenAI calls
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1

# Entity that stores the last query result
RESULT_ENTITY = "rag_search.last_query_result"
