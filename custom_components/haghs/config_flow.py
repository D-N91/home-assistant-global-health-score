import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import os

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    CONF_STORAGE_TYPE,
    CONF_LOG_FILE,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_STORAGE_TYPE,
    STORAGE_TYPES,
)

class HaghsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HAGHS."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate Log File if provided
            log_path = user_input.get(CONF_LOG_FILE)
            if log_path and not os.path.isfile(log_path):
                # Check if we can access it (might be permission issue, but simple check first)
                if not os.path.exists(log_path):
                     errors["base"] = "invalid_path"
            
            if not errors:
                return self.async_create_entry(title="Global Health Score", data=user_input)

        # Schema for Setup
        data_schema = vol.Schema({
            vol.Required(CONF_STORAGE_TYPE, default=DEFAULT_STORAGE_TYPE): selector.SelectSelector(
                selector.SelectSelectorConfig(options=STORAGE_TYPES),
            ),
            vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
            vol.Optional(CONF_LOG_FILE): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HaghsOptionsFlowHandler(config_entry)


class HaghsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for HAGHS (Re-Configure)."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}

        if user_input is not None:
            # Update the entry
            return self.async_create_entry(title="", data=user_input)

        # Load current values
        current_storage = self.config_entry.options.get(CONF_STORAGE_TYPE, self.config_entry.data.get(CONF_STORAGE_TYPE, DEFAULT_STORAGE_TYPE))
        current_interval = self.config_entry.options.get(CONF_UPDATE_INTERVAL, self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))
        current_log = self.config_entry.options.get(CONF_LOG_FILE, self.config_entry.data.get(CONF_LOG_FILE, ""))

        options_schema = vol.Schema({
            vol.Required(CONF_STORAGE_TYPE, default=current_storage): selector.SelectSelector(
                selector.SelectSelectorConfig(options=STORAGE_TYPES),
            ),
            vol.Required(CONF_UPDATE_INTERVAL, default=current_interval): int,
            vol.Optional(CONF_LOG_FILE, description={"suggested_value": current_log}): str,
        })

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
