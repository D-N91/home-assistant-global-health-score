"""Config flow and options flow for HAGHS integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import PERCENTAGE
from homeassistant.helpers import selector

from .const import (
    CONF_CPU_SENSOR,
    CONF_DB_SENSOR,
    CONF_IGNORE_LABEL,
    CONF_RAM_SENSOR,
    CONF_STORAGE_TYPE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_STORAGE_TYPE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    STORAGE_TYPES,
)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CPU_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(
                filter=(
                    selector.EntityFilterSelectorConfig(
                        domain="sensor", unit_of_measurement=PERCENTAGE
                    )
                )
            )
        ),
        vol.Required(CONF_RAM_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(
                filter=(
                    selector.EntityFilterSelectorConfig(
                        domain="sensor", unit_of_measurement=PERCENTAGE
                    )
                )
            )
        ),
        vol.Required(
            CONF_STORAGE_TYPE, default=DEFAULT_STORAGE_TYPE
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=STORAGE_TYPES,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(
            CONF_IGNORE_LABEL
        ): selector.LabelSelector(),
        vol.Optional(CONF_DB_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(
                filter=selector.EntityFilterSelectorConfig(domain="sensor")
            )
        ),
        vol.Optional(
            CONF_UPDATE_INTERVAL,
            default=DEFAULT_UPDATE_INTERVAL,
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=10,
                max=3600,
                step=1,
                unit_of_measurement="s",
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
    }
)


class HaghsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HAGHS."""

    VERSION = 3

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HaghsOptionsFlowHandler:
        """Return the options flow handler."""
        return HaghsOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Global Health Score", data=user_input)

        return self.async_show_form(step_id="user", data_schema=SCHEMA)


class HaghsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle HAGHS options — storage type, ignore label, update interval."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Current values: options take priority, then data, then defaults
        current = {**self._config_entry.data, **self._config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(SCHEMA, current),
        )
