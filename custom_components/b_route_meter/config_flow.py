"""Config Flow for B-Route Meter.

This implements the UI wizard to let user input B-route ID, password,
serial port and adapter model in Home Assistant's "Integrations" page.
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_MODEL,
    CONF_RETRY_COUNT,
    CONF_ROUTE_B_ID,
    CONF_ROUTE_B_PWD,
    CONF_SERIAL_PORT,
    DEFAULT_MODEL,
    DEFAULT_RETRY_COUNT,
    DEFAULT_SERIAL_PORT,
    DOMAIN,
    SUPPORTED_MODELS,
)

# We define the user step schema
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ROUTE_B_ID): str,
        vol.Required(CONF_ROUTE_B_PWD): str,
        vol.Required(CONF_MODEL, default=DEFAULT_MODEL): vol.In(SUPPORTED_MODELS),
        vol.Optional(CONF_SERIAL_PORT, default=DEFAULT_SERIAL_PORT): str,
        vol.Optional(CONF_RETRY_COUNT, default=str(DEFAULT_RETRY_COUNT)): str,
    }
)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for B-Route Meter."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self.entry = config_entry

    async def async_step_init(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            try:
                user_input = {
                    **user_input,
                    CONF_RETRY_COUNT: int(user_input[CONF_RETRY_COUNT]),
                }

                if not 1 <= user_input[CONF_RETRY_COUNT] <= 10:
                    errors[CONF_RETRY_COUNT] = "invalid_retry_count"
                else:
                    return self.async_create_entry(title="", data=user_input)
            except ValueError:
                errors[CONF_RETRY_COUNT] = "invalid_retry_count"

        all_current = {**self.config_entry.data, **self.config_entry.options}

        schema = {
            vol.Optional(
                CONF_SERIAL_PORT,
                default=all_current.get(CONF_SERIAL_PORT, DEFAULT_SERIAL_PORT),
            ): str,
            vol.Optional(
                CONF_RETRY_COUNT,
                default=str(all_current.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT)),
            ): str,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors,
        )


class BRouteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for B-Route Meter."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Ensure retry_count is an integer
                user_input = {
                    **user_input,
                    CONF_RETRY_COUNT: int(user_input[CONF_RETRY_COUNT]),
                }

                unique_id = user_input[CONF_ROUTE_B_ID]
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                if not (1 <= user_input[CONF_RETRY_COUNT] <= 10):
                    errors[CONF_RETRY_COUNT] = "invalid_retry_count"
                else:
                    return self.async_create_entry(
                        title=f"B-Route Meter ({unique_id})",
                        data=user_input,
                    )
            except ValueError:
                errors[CONF_RETRY_COUNT] = "invalid_retry_count"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, str] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        if user_input is not None:
            self.async_set_unique_id(user_input[CONF_ROUTE_B_ID])
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=STEP_USER_DATA_SCHEMA,
        )

    def _get_reconfigure_entry(self) -> config_entries.ConfigEntry:
        """Get the current config entry."""
        if self.unique_id is None:
            return None
        for entry in self._async_current_entries():
            if entry.unique_id == self.unique_id:
                return entry
        return None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)
