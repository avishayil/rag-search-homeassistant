"""Tests for the RAG Search config flow."""

from aioresponses import aioresponses
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.rag_search.const import (
    CONF_ENTITY_SCOPE,
    CONF_MAX_ITEMS,
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    DOMAIN,
    OPENAI_MODELS_URL,
)

USER_INPUT = {
    CONF_OPENAI_API_KEY: "sk-test-key",
    CONF_OPENAI_MODEL: "gpt-4o-mini",
    CONF_ENTITY_SCOPE: ["sensor.temperature"],
    CONF_MAX_ITEMS: 25,
}


async def test_user_flow_happy_path(hass: HomeAssistant):
    """A valid API key creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    with aioresponses() as mocked:
        mocked.get(OPENAI_MODELS_URL, status=200, payload={"data": []})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "RAG Search"
    assert result["data"][CONF_OPENAI_API_KEY] == "sk-test-key"
    assert result["data"][CONF_OPENAI_MODEL] == "gpt-4o-mini"


async def test_user_flow_invalid_auth(hass: HomeAssistant):
    """A rejected API key shows an invalid_auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with aioresponses() as mocked:
        mocked.get(OPENAI_MODELS_URL, status=401, payload={"error": "bad key"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass: HomeAssistant):
    """A connection error shows a cannot_connect error."""
    import aiohttp

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with aioresponses() as mocked:
        mocked.get(OPENAI_MODELS_URL, exception=aiohttp.ClientError("boom"))
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_import_flow_creates_entry(hass: HomeAssistant):
    """YAML import creates an entry without network validation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_OPENAI_API_KEY] == "sk-test-key"


async def test_single_instance_only(hass: HomeAssistant):
    """A second config flow aborts because the domain is single-instance."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=USER_INPUT,
    )
    await hass.async_block_till_done()
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
