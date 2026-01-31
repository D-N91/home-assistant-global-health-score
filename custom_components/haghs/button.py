"""Button platform for HAGHS."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, DEFAULT_NAME

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HAGHS button platform."""
    async_add_entities([HaghsRecalculateButton(entry)], update_before_add=True)

class HaghsRecalculateButton(ButtonEntity):
    """Button to force a HAGHS score recalculation."""

    def __init__(self, entry):
        """Initialize the button."""
        self.entry = entry
        self._attr_name = f"Recalculate {DEFAULT_NAME}"
        self._attr_unique_id = f"{entry.entry_id}_recalculate_button"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        # Sucht den HAGHS Sensor und erzwingt ein Update
        ent_reg = er.async_get(self.hass)
        # Wir suchen die Entity-ID des Sensors basierend auf der Unique ID
        sensor_unique_id = f"{self.entry.entry_id}_score"
        entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, sensor_unique_id)
        
        if entity_id:
            await self.hass.services.async_call(
                "homeassistant",
                "update_entity",
                {"entity_id": entity_id},
                blocking=True,
            )
