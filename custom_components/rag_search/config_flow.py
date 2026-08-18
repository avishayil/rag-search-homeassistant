"""Config flow for the RAG Search integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ENTITY_SCOPE,
    CONF_MAX_ITEMS,
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    DEFAULT_MAX_ITEMS,
    DEFAULT_MODEL,
    DOMAIN,
    OPENAI_MODELS_URL,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_api_key(hass, api_key: str) -> None:
    """Validate the OpenAI API key.

    Raises ``InvalidAuth`` if the key is rejected and ``CannotConnect`` if the
    OpenAI API cannot be reached.
    """
    session = async_get_clientsession(hass)
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with session.get(
            OPENAI_MODELS_URL,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
        ) as response:
            if response.status in (401, 403):
                raise InvalidAuth
            if response.status != 200:
                _LOGGER.error(
                    "Unexpected status validating OpenAI key: %s", response.status
                )
                raise CannotConnect
    except aiohttp.ClientError as err:
        _LOGGER.error("Error connecting to OpenAI: %s", err)
        raise CannotConnect from err


def _user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the user/import form schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_OPENAI_API_KEY,
                default=defaults.get(CONF_OPENAI_API_KEY, ""),
            ): cv.string,
            vol.Optional(
                CONF_OPENAI_MODEL,
                default=defaults.get(CONF_OPENAI_MODEL, DEFAULT_MODEL),
            ): cv.string,
            vol.Optional(
                CONF_ENTITY_SCOPE,
                default=defaults.get(CONF_ENTITY_SCOPE, []),
            ): cv.ensure_list,
            vol.Optional(
                CONF_MAX_ITEMS,
                default=defaults.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS),
            ): cv.positive_int,
        }
    )


class RagSearchConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RAG Search."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial UI step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _validate_api_key(self.hass, user_input[CONF_OPENAI_API_KEY])
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="RAG Search", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=_user_schema(user_input), errors=errors
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Import configuration from configuration.yaml."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        # We intentionally skip network validation on import so that a valid
        # existing YAML setup keeps working even if OpenAI is briefly
        # unreachable at startup.
        return self.async_create_entry(title="RAG Search (YAML)", data=import_data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return RagSearchOptionsFlow(config_entry)


class RagSearchOptionsFlow(OptionsFlow):
    """Handle options for RAG Search (model, scope, limits)."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._config_entry.data, **self._config_entry.options}
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_OPENAI_MODEL,
                    default=current.get(CONF_OPENAI_MODEL, DEFAULT_MODEL),
                ): cv.string,
                vol.Optional(
                    CONF_ENTITY_SCOPE,
                    default=current.get(CONF_ENTITY_SCOPE, []),
                ): cv.ensure_list,
                vol.Optional(
                    CONF_MAX_ITEMS,
                    default=current.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS),
                ): cv.positive_int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class CannotConnect(Exception):
    """Error to indicate we cannot connect to OpenAI."""


class InvalidAuth(Exception):
    """Error to indicate the OpenAI API key is invalid."""
