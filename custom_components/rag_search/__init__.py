import logging
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from homeassistant.core import ServiceCall
from aiohttp import ClientSession
from .search import search_history
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required("openai_api_key"): cv.string,
                vol.Optional("openai_model", default="gpt-4-turbo"): cv.string,
                vol.Required("entity_scope", default=[]): cv.ensure_list(cv.entity_id),
                vol.Optional("max_items", default=50): cv.positive_int,
                vol.Optional("timeout", default=15): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up the RAG Search component."""
    conf = config[DOMAIN]
    entity_scope = conf.get("entity_scope", [])
    invalid_entities = [
        entity for entity in entity_scope if not hass.states.get(entity)
    ]
    if invalid_entities:
        _LOGGER.warning(
            "Some entities in entity_scope are invalid: %s", invalid_entities
        )

    hass.data[DOMAIN] = {
        "session": ClientSession(),
    }

    # Register the service
    async def handle_search_history(call: ServiceCall):
        entity_id = call.data.get("entity_id")
        if entity_id not in entity_scope:
            _LOGGER.error("Entity %s is not in the allowed scope.", entity_id)
            hass.states.async_set(
                "rag_search.last_query_result", "Entity not in scope."
            )
            return
        await search_history(hass, config, call)

    hass.services.async_register(DOMAIN, "search_history", handle_search_history)

    _LOGGER.info(
        "Service %s.search_history registered with entity scope: %s.",
        DOMAIN,
        entity_scope,
    )

    return True


async def async_unload_entry(hass, entry):
    """Unload the RAG Search component."""
    session = hass.data[DOMAIN]["session"]
    await session.close()
    return True
