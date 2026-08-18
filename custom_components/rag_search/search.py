"""RAG history search logic for the RAG Search integration."""

import asyncio
import logging
from datetime import datetime

import aiohttp
from homeassistant.components.recorder import get_instance, history
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    CONF_MAX_ITEMS,
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    DEFAULT_MAX_ITEMS,
    DEFAULT_MODEL,
    DOMAIN,
    MAX_RETRIES,
    OPENAI_CHAT_URL,
    OPENAI_MAX_TOKENS,
    REQUEST_TIMEOUT,
    RESULT_ENTITY,
    RETRY_BACKOFF_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


def _parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 timestamp, tolerating a trailing ``Z``."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format_history(entity_id: str, history_data: dict, num_items: int) -> list[str]:
    """Format significant-state history into human-readable lines."""
    entries: list[str] = []
    if entity_id in history_data:
        latest_entries = history_data[entity_id][-num_items:]
        for state in latest_entries:
            entries.append(
                f"{state.entity_id} changed to {state.state} at {state.last_changed}"
            )
    return entries


async def _call_openai(
    session: aiohttp.ClientSession, api_key: str, model: str, prompt: str
) -> str | None:
    """Call the OpenAI chat completions API with timeout and retries.

    Returns the answer text, or ``None`` on a non-retryable failure.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": OPENAI_MAX_TOKENS,
    }
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.post(
                OPENAI_CHAT_URL, json=payload, headers=headers, timeout=timeout
            ) as response:
                # 4xx (except 429) are client errors and will not succeed on
                # retry, so fail fast.
                if response.status == 429 or response.status >= 500:
                    _LOGGER.warning(
                        "OpenAI API returned retryable status %s (attempt %d/%d)",
                        response.status,
                        attempt,
                        MAX_RETRIES,
                    )
                    last_error = RuntimeError(f"status {response.status}")
                    await _backoff(attempt)
                    continue
                if response.status != 200:
                    _LOGGER.error(
                        "OpenAI API returned a non-200 status: %s", response.status
                    )
                    return None

                response_data = await response.json()
                choices = response_data.get("choices")
                if not choices:
                    _LOGGER.error("Invalid response from OpenAI: %s", response_data)
                    return None
                return choices[0]["message"]["content"].strip()

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            last_error = err
            _LOGGER.warning(
                "Error calling OpenAI API (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                err,
            )
            await _backoff(attempt)

    _LOGGER.error(
        "OpenAI API call failed after %d attempts: %s", MAX_RETRIES, last_error
    )
    return None


async def _backoff(attempt: int) -> None:
    """Sleep with linear backoff between retries (skipped on the last attempt)."""
    if attempt < MAX_RETRIES:
        await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)


async def search_history(hass: HomeAssistant, conf: dict, call: ServiceCall) -> None:
    """Handle the service call for rag_search.search_history."""
    openai_model = conf.get(CONF_OPENAI_MODEL, DEFAULT_MODEL)
    openai_api_key = conf.get(CONF_OPENAI_API_KEY)
    max_items = conf.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS)
    session = hass.data[DOMAIN]["session"]

    start_time_str = call.data.get("start_time")
    end_time_str = call.data.get("end_time")
    if not start_time_str or not end_time_str:
        _LOGGER.error("Both 'start_time' and 'end_time' must be provided.")
        hass.states.async_set(RESULT_ENTITY, "Invalid time parameters.")
        return

    try:
        start_time = _parse_iso(start_time_str)
        end_time = _parse_iso(end_time_str)
    except ValueError as err:
        _LOGGER.error("Invalid date format for start_time or end_time: %s", err)
        hass.states.async_set(RESULT_ENTITY, "Invalid date format.")
        return

    entity_id = call.data.get("entity_id")
    if isinstance(entity_id, list):
        entity_id = entity_id[0] if entity_id else None

    num_items = min(call.data.get("num_items", max_items), max_items)

    _LOGGER.debug(
        "Fetching history from %s to %s for entity %s",
        start_time,
        end_time,
        entity_id,
    )
    history_data = await get_instance(hass).async_add_executor_job(
        history.get_significant_states, hass, start_time, end_time, [entity_id]
    )

    history_entries = _format_history(entity_id, history_data, num_items)
    _LOGGER.info("Collected %d history entries.", len(history_entries))

    prompt = (
        "\n".join(history_entries) + "\n\nUser Query: " + str(call.data.get("query"))
    )
    _LOGGER.debug("Generated prompt for OpenAI: %s", prompt)

    answer = await _call_openai(session, openai_api_key, openai_model, prompt)
    if answer is None:
        hass.states.async_set(RESULT_ENTITY, "Error processing the query.")
        return

    _LOGGER.info("Received response from OpenAI: %s", answer)
    hass.states.async_set(RESULT_ENTITY, answer)
