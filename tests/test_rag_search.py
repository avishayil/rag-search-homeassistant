"""Test component setup and functionality."""

from homeassistant.setup import async_setup_component
from custom_components.rag_search.const import DOMAIN
from homeassistant.core import HomeAssistant
from unittest.mock import patch, AsyncMock


async def test_search_history_not_in_scope(hass: HomeAssistant):
    """Test calling the service with an entity that is not in scope."""
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

    with patch("homeassistant.core.ServiceCall") as mock_service_call:
        mock_service_call.data = {
            "entity_id": "light.living_room",
            "start_time": "2024-10-01T00:00:00Z",
            "end_time": "2024-10-10T23:59:59Z",
            "query": "What was the state?",
        }

        await hass.services.async_call(
            DOMAIN, "search_history", mock_service_call.data, blocking=True
        )
        state = hass.states.get("rag_search.last_query_result")
        assert state.state == "Entity not in scope."


async def test_search_history_api_call(hass: HomeAssistant):
    """Test search_history service making a successful API call."""
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

    with patch("aiohttp.ClientSession.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"choices": [{"message": {"content": "Test Response"}}]}
        )

        await hass.services.async_call(
            DOMAIN,
            "search_history",
            {
                "entity_id": "sensor.temperature",
                "start_time": "2024-10-01T00:00:00Z",
                "end_time": "2024-10-10T23:59:59Z",
                "query": "What was the state?",
            },
            blocking=True,
        )

        state = hass.states.get("rag_search.last_query_result")
        assert state.state == "Test Response"


async def test_invalid_time_format(hass: HomeAssistant):
    """Test search_history service with invalid time format."""
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

    with patch("homeassistant.core.ServiceCall") as mock_service_call:
        mock_service_call.data = {
            "entity_id": "sensor.temperature",
            "start_time": "invalid_time",
            "end_time": "2024-10-10T23:59:59Z",
            "query": "What was the state?",
        }

        await hass.services.async_call(
            DOMAIN, "search_history", mock_service_call.data, blocking=True
        )
        state = hass.states.get("rag_search.last_query_result")
        assert state.state == "Invalid date format."
