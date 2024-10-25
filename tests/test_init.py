"""Test component setup."""

from homeassistant.setup import async_setup_component
from homeassistant.core import HomeAssistant
from custom_components.rag_search.const import DOMAIN


async def test_async_setup(hass: HomeAssistant):
    """Test the component gets setup."""
    assert (
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "openai_api_key": "fake_api_key",
                    "entity_scope": ["sensor.temperature"],
                    "max_items": 50,
                }
            },
        )
        is True
    )


async def test_service_registration(hass: HomeAssistant):
    """Test that the search_history service is registered."""
    await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "openai_api_key": "fake_api_key",
                "entity_scope": ["sensor.temperature"],
            }
        },
    )
    assert hass.services.has_service(DOMAIN, "search_history")
