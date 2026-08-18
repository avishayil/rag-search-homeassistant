"""Fixtures for testing the RAG Search integration."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.rag_search.const import (
    CONF_ENTITY_SCOPE,
    CONF_MAX_ITEMS,
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for every test."""
    return


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a mock config entry for RAG Search."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="RAG Search",
        unique_id=DOMAIN,
        data={
            CONF_OPENAI_API_KEY: "fake_api_key",
            CONF_OPENAI_MODEL: "gpt-4o-mini",
            CONF_ENTITY_SCOPE: ["sensor.temperature"],
            CONF_MAX_ITEMS: 50,
        },
    )


@pytest.fixture
async def setup_integration(hass, config_entry):
    """Add the config entry to hass and set it up."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
