"""Config flow for HAGHS integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_CPU_SENSOR,
    CONF_RAM_SENSOR,
    CONF_DISK_SENSOR,
    CONF_DB_SENSOR,
    CONF_CORE_UPDATE_ENTITY,
    CONF_IGNORE_LABEL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)

class HaghsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HAGHS."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="HAGHS Advisor", data=user_input)

        # Definition der Felder im Setup-Dialog
        data_schema = vol.Schema({
            vol.Required(CONF_CPU_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="power_factor") # Oder passend
            ),
            vol.Optional(CONF_TEMP_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Optional(CONF_LATENCY_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_RAM_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_DISK_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_DB_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_CORE_UPDATE_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="update")
            ),
            vol.Required(CONF_IGNORE_LABEL): selector.LabelSelector(),
            # NEU: Auswahl des Intervalls
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.In([1, 2, 5, 10, 30, 60]),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)
