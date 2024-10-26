import logging
import aiohttp
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.components.recorder import history
from datetime import datetime
from aiohttp import ClientTimeout, ClientConnectionError, ClientResponseError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def search_history(hass: HomeAssistant, config, call: ServiceCall):
    """Handle the service call for rag_search.search_history."""
    conf = config[DOMAIN]
    openai_model = conf.get("openai_model", "gpt-4-turbo")
    openai_api_key = conf.get("openai_api_key")
    max_items = conf.get("max_items", 50)
    timeout_value = conf.get("timeout", 15)
    session = hass.data[DOMAIN]["session"]

    # Extract start_time and end_time safely
    start_time_str = call.data.get("start_time")
    end_time_str = call.data.get("end_time")

    if not start_time_str or not end_time_str:
        _LOGGER.error("Both 'start_time' and 'end_time' must be provided.")
        hass.states.async_set(
            "rag_search.last_query_result", "Invalid time parameters."
        )
        return

    try:
        start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
    except ValueError as e:
        _LOGGER.error("Invalid date format for start_time or end_time: %s", e)
        hass.states.async_set("rag_search.last_query_result", "Invalid date format.")
        return

    entity_id = call.data.get("entity_id", None)
    if isinstance(entity_id, list):
        entity_id = entity_id[0] if entity_id else None

    num_items = call.data.get("num_items", max_items)
    num_items = min(num_items, max_items)

    # Get history data from Home Assistant
    _LOGGER.debug(
        "Fetching history from %s to %s for entity %s", start_time, end_time, entity_id
    )
    from homeassistant.components.recorder import get_instance

    history_data = await get_instance(hass).async_add_executor_job(
        history.get_significant_states, hass, start_time, end_time, [entity_id]
    )

    history_entries = []
    if entity_id in history_data:
        entity_states = history_data[entity_id]
        latest_entries = entity_states[-num_items:]  # Get the last num_items entries

        for state in latest_entries:
            entry = (
                f"{state.entity_id} changed to {state.state} at {state.last_changed}"
            )
            history_entries.append(entry)

    _LOGGER.info("Collected %d history entries.", len(history_entries))

    # Embed history data in a prompt and call OpenAI API
    prompt = "\n".join(history_entries) + "\n\nUser Query: " + call.data.get("query")
    _LOGGER.debug("Generated prompt for OpenAI: %s", prompt)

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": openai_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
    }

    answer = await call_openai_api(session, headers, payload, timeout_value, hass)
    if answer:
        result_entity_id = f"rag_search.query_result.{entity_id}"
        hass.states.async_set(result_entity_id, answer)


async def call_openai_api(session, headers, payload, timeout_value, hass):
    """Helper function to call the OpenAI API."""
    try:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=ClientTimeout(total=timeout_value),
        ) as response:
            if response.status != 200:
                _LOGGER.error(
                    "OpenAI API returned a non-200 status: %s", response.status
                )
                hass.states.async_set(
                    "rag_search.last_query_result", "OpenAI API error."
                )
                return None

            response_data = await response.json()
            _LOGGER.debug("Received response from OpenAI: %s", response_data)

            if "choices" not in response_data or not response_data["choices"]:
                _LOGGER.error("Invalid response from OpenAI: %s", response_data)
                hass.states.async_set(
                    "rag_search.last_query_result", "Invalid response from OpenAI."
                )
                return None

            answer = response_data["choices"][0]["message"]["content"].strip()
            _LOGGER.info("Received response from OpenAI: %s", answer)
            return answer

    except ClientConnectionError as e:
        _LOGGER.error("Connection error while calling OpenAI API: %s", e)
        hass.states.async_set(
            "rag_search.last_query_result",
            "Connection error while processing the query.",
        )
    except ClientResponseError as e:
        _LOGGER.error("Client error while calling OpenAI API: %s", e)
        hass.states.async_set(
            "rag_search.last_query_result", f"Client error: {e.message}"
        )
    except aiohttp.ClientError as e:
        _LOGGER.error("Error while calling OpenAI API: %s", e)
        hass.states.async_set(
            "rag_search.last_query_result", "Network error processing the query."
        )
    except Exception as e:
        _LOGGER.error("Unexpected error: %s", e)
        hass.states.async_set(
            "rag_search.last_query_result", "Error processing the query."
        )
    return None
