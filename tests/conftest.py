"""Fixtures for testing."""

import pytest
from pytest_socket import enable_socket
from homeassistant.setup import setup_component
from homeassistant.core import HomeAssistant
from custom_components.rag_search.const import DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return enable_custom_integrations


@pytest.fixture(autouse=True)
def enable_socket_fixture():
    """Enable sockets."""
    enable_socket()


@pytest.fixture(autouse=True)
async def ha_setup_component(hass: HomeAssistant):
    """Set up the RAG Search component."""
    config = {
        DOMAIN: {
            "openai_api_key": "test_api_key",
            "openai_model": "gpt-4-turbo",
            "entity_scope": ["sensor.test_sensor"],
            "max_items": 5,
            "timeout": 15,
        }
    }
    assert setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
