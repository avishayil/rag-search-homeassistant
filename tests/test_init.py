"""Tests for the RAG Search component."""

from unittest.mock import AsyncMock, patch
import pytest
from homeassistant.core import HomeAssistant
from custom_components.rag_search.const import DOMAIN


@pytest.mark.asyncio
async def test_search_history_valid_entity(
    hass: HomeAssistant, ha_setup_component, aioclient_mock
):
    """Test the search_history service with a valid entity."""
    with patch("custom_components.rag_search.search.get_instance") as mock_get_instance:
        mock_get_instance.return_value.async_add_executor_job = AsyncMock(
            return_value={"sensor.test_sensor": []}
        )

        # Mocking the aiohttp call to OpenAI API
        aioclient_mock.post(
            "https://api.openai.com/v1/chat/completions",
            json={"choices": [{"message": {"content": "test response"}}]},
        )

        await hass.services.async_call(
            DOMAIN,
            "search_history",
            {
                "entity_id": "sensor.test_sensor",
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z",
                "query": "What happened?",
            },
            blocking=True,
        )

        state = hass.states.get("rag_search.query_result.sensor.test_sensor")
        assert state is not None
        assert state.state == "test response"


# @pytest.mark.asyncio
# async def test_search_history_invalid_entity(hass: HomeAssistant, ha_setup_component):
#     """Test the search_history service with an entity not in the allowed scope."""
#     await hass.services.async_call(
#         DOMAIN,
#         "search_history",
#         {
#             "entity_id": "sensor.invalid_sensor",
#             "start_time": "2024-01-01T00:00:00Z",
#             "end_time": "2024-01-02T00:00:00Z",
#             "query": "What happened?",
#         },
#         blocking=True,
#     )

#     state = hass.states.get("rag_search.last_query_result")
#     assert state is not None
#     assert state.state == "Entity not in scope."


# @pytest.mark.asyncio
# async def test_search_history_invalid_time_format(hass: HomeAssistant, ha_setup_component):
#     """Test the search_history service with invalid time format."""
#     await hass.services.async_call(
#         DOMAIN,
#         "search_history",
#         {
#             "entity_id": "sensor.test_sensor",
#             "start_time": "invalid_time",
#             "end_time": "2024-01-02T00:00:00Z",
#             "query": "What happened?",
#         },
#         blocking=True,
#     )

#     state = hass.states.get("rag_search.last_query_result")
#     assert state is not None
#     assert state.state == "Invalid date format."


# @pytest.mark.asyncio
# async def test_openai_api_error(hass, ha_setup_component, aioclient_mock):
#     """Test the call to OpenAI API that returns an error."""
#     with patch("custom_components.rag_search.search.get_instance") as mock_get_instance:
#         mock_get_instance.return_value.async_add_executor_job = AsyncMock(
#             return_value={"sensor.test_sensor": []}
#         )

#         # Simulate OpenAI API failure
#         aioclient_mock.post(
#             "https://api.openai.com/v1/chat/completions",
#             status=500,
#             json={"error": "API error"},
#         )

#         await hass.services.async_call(
#             DOMAIN,
#             "search_history",
#             {
#                 "entity_id": "sensor.test_sensor",
#                 "start_time": "2024-01-01T00:00:00Z",
#                 "end_time": "2024-01-02T00:00:00Z",
#                 "query": "What happened?",
#             },
#             blocking=True,
#         )

#         state = hass.states.get("rag_search.last_query_result")
#         assert state is not None
#         assert state.state == "OpenAI API error."
