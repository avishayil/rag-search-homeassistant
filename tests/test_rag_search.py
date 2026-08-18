"""Test the rag_search.search_history service end to end (OpenAI mocked)."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
from aioresponses import aioresponses
from homeassistant.core import HomeAssistant

from custom_components.rag_search.const import (
    DOMAIN,
    OPENAI_CHAT_URL,
    RESULT_ENTITY,
    SERVICE_SEARCH_HISTORY,
)

CALL_DATA = {
    "entity_id": "sensor.temperature",
    "start_time": "2024-10-01T00:00:00Z",
    "end_time": "2024-10-10T23:59:59Z",
    "query": "What was the state?",
}


def _patch_history(return_value=None):
    """Patch the recorder history lookup used by search_history."""
    instance = MagicMock()
    instance.async_add_executor_job = AsyncMock(return_value=return_value or {})
    return patch(
        "custom_components.rag_search.search.get_instance", return_value=instance
    )


async def _call(hass: HomeAssistant, data: dict) -> str:
    await hass.services.async_call(DOMAIN, SERVICE_SEARCH_HISTORY, data, blocking=True)
    await hass.async_block_till_done()
    return hass.states.get(RESULT_ENTITY).state


async def test_not_in_scope(hass: HomeAssistant, setup_integration):
    """An entity outside the scope is rejected before any API call."""
    result = await _call(hass, {**CALL_DATA, "entity_id": "light.living_room"})
    assert result == "Entity not in scope."


async def test_invalid_time_format(hass: HomeAssistant, setup_integration):
    """A bad timestamp is reported without calling OpenAI."""
    with _patch_history():
        result = await _call(hass, {**CALL_DATA, "start_time": "not-a-date"})
    assert result == "Invalid date format."


async def test_missing_time(hass: HomeAssistant, setup_integration):
    """Missing time parameters are reported."""
    data = {k: v for k, v in CALL_DATA.items() if k != "end_time"}
    with _patch_history():
        result = await _call(hass, data)
    assert result == "Invalid time parameters."


async def test_successful_api_call(hass: HomeAssistant, setup_integration):
    """A successful OpenAI response is stored as the result."""
    with _patch_history(), aioresponses() as mocked:
        mocked.post(
            OPENAI_CHAT_URL,
            status=200,
            payload={"choices": [{"message": {"content": "  Test Response  "}}]},
        )
        result = await _call(hass, CALL_DATA)
    assert result == "Test Response"


async def test_openai_client_error(hass: HomeAssistant, setup_integration):
    """A persistent network error yields an error result after retries."""
    with _patch_history(), aioresponses() as mocked:
        # aioresponses replays the exception once per matched call; register
        # enough for all retry attempts.
        for _ in range(5):
            mocked.post(OPENAI_CHAT_URL, exception=aiohttp.ClientError("boom"))
        with patch("custom_components.rag_search.search.asyncio.sleep", AsyncMock()):
            result = await _call(hass, CALL_DATA)
    assert result == "Error processing the query."


async def test_openai_timeout(hass: HomeAssistant, setup_integration):
    """A timeout is retried and then reported as an error."""
    import asyncio

    with _patch_history(), aioresponses() as mocked:
        for _ in range(5):
            mocked.post(OPENAI_CHAT_URL, exception=asyncio.TimeoutError())
        with patch("custom_components.rag_search.search.asyncio.sleep", AsyncMock()):
            result = await _call(hass, CALL_DATA)
    assert result == "Error processing the query."


async def test_openai_bad_payload(hass: HomeAssistant, setup_integration):
    """A 200 response with no choices is treated as an error."""
    with _patch_history(), aioresponses() as mocked:
        mocked.post(OPENAI_CHAT_URL, status=200, payload={"choices": []})
        result = await _call(hass, CALL_DATA)
    assert result == "Error processing the query."
