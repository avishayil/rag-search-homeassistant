"""Test component setup and teardown via config entries."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.rag_search.const import DOMAIN, SERVICE_SEARCH_HISTORY


async def test_setup_entry(hass: HomeAssistant, setup_integration):
    """The config entry loads and stores its resolved config."""
    entry = setup_integration
    assert entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert hass.data[DOMAIN]["config"]["openai_model"] == "gpt-4o-mini"


async def test_service_registration(hass: HomeAssistant, setup_integration):
    """The search_history service is registered on setup."""
    assert hass.services.has_service(DOMAIN, SERVICE_SEARCH_HISTORY)


async def test_unload_entry(hass: HomeAssistant, setup_integration):
    """Unloading the entry removes the service and its data."""
    entry = setup_integration
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not hass.services.has_service(DOMAIN, SERVICE_SEARCH_HISTORY)
    assert DOMAIN not in hass.data
