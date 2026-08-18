"""The RAG Search integration."""

import logging

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ENTITY_SCOPE,
    CONF_MAX_ITEMS,
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    DEFAULT_MAX_ITEMS,
    DEFAULT_MODEL,
    DOMAIN,
    RESULT_ENTITY,
    SERVICE_SEARCH_HISTORY,
)
from .search import search_history

_LOGGER = logging.getLogger(__name__)

# YAML schema kept for backwards compatibility. New installs should use the UI
# config flow; any YAML present is imported into a config entry on startup.
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_OPENAI_API_KEY): cv.string,
                vol.Optional(CONF_OPENAI_MODEL, default=DEFAULT_MODEL): cv.string,
                vol.Required(CONF_ENTITY_SCOPE, default=[]): cv.ensure_list(
                    cv.entity_id
                ),
                vol.Optional(
                    CONF_MAX_ITEMS, default=DEFAULT_MAX_ITEMS
                ): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Import YAML configuration into a config entry (back-compat)."""
    if DOMAIN not in config:
        return True

    _LOGGER.warning(
        "Configuring %s via configuration.yaml is deprecated and will be imported "
        "into the UI. Your OpenAI API key is now stored securely; you can remove "
        "the YAML block after Home Assistant restarts.",
        DOMAIN,
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    )
    return True


def _resolve_config(entry: ConfigEntry) -> dict:
    """Merge entry data and options into a single config dict."""
    merged = {**entry.data, **entry.options}
    return {
        CONF_OPENAI_API_KEY: merged.get(CONF_OPENAI_API_KEY),
        CONF_OPENAI_MODEL: merged.get(CONF_OPENAI_MODEL, DEFAULT_MODEL),
        CONF_ENTITY_SCOPE: merged.get(CONF_ENTITY_SCOPE, []),
        CONF_MAX_ITEMS: merged.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS),
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RAG Search from a config entry."""
    conf = _resolve_config(entry)
    entity_scope = conf[CONF_ENTITY_SCOPE]

    # Use Home Assistant's shared aiohttp client session so we do not leak
    # sessions and it is closed by HA on shutdown.
    session = async_get_clientsession(hass)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {"session": session, "config": conf}

    async def handle_search_history(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        if entity_id not in entity_scope:
            _LOGGER.error("Entity %s is not in the allowed scope.", entity_id)
            hass.states.async_set(RESULT_ENTITY, "Entity not in scope.")
            return
        await search_history(hass, conf, call)

    hass.services.async_register(DOMAIN, SERVICE_SEARCH_HISTORY, handle_search_history)
    _LOGGER.info("Service %s.%s registered.", DOMAIN, SERVICE_SEARCH_HISTORY)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, SERVICE_SEARCH_HISTORY)
    hass.data.pop(DOMAIN, None)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
