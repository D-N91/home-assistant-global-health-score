"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta
import os

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ICON_OK = "mdi:check-circle"
ICON_WARN = "mdi:alert-circle"
ICON_CRIT = "mdi:alert-octagon"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities([HaghsSensor(hass, entry)], update_before_add=True)


class HaghsSensor(SensorEntity):
    """Representation of the HAGHS Sensor."""

    _attr_name = "HAGHS Score"
    _attr_icon = "mdi:heart-pulse"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the sensor."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_score"
        
        # Config Data
        self._storage_type = config_entry.data.get("storage_type", "SD Card")
        self._update_interval = config_entry.data.get("update_interval", 60)
        self._log_file_path = config_entry.data.get("log_file", "")

        # Internal State
        self._score = 100
        self._recommendations = []
        self._unsub_timer = None

        # Recorder Purge Service (Specific anchor)
        self.LINK_DB = "https://www.home-assistant.io/integrations/recorder/#service-recorderpurge"
        # Recorder Integration (General settings)
        self.LINK_RECORDER = "https://www.home-assistant.io/integrations/recorder/"
        # Troubleshooting (Unavailable entities)
        self.LINK_ZOMBIES = "https://www.home-assistant.io/docs/configuration/troubleshooting/"
        # Common Tasks OS (Moving data disk / freeing space) - Best fallback for storage issues
        self.LINK_STORAGE = "https://www.home-assistant.io/common-tasks/os/"

    async def async_added_to_hass(self):
        """Handle when entity is added to Home Assistant."""
        # Set Update Interval
        interval = timedelta(minutes=int(self._update_interval))
        self._unsub_timer = async_track_time_interval(
            self.hass, self._update_logic, interval
        )
        
        # Initial Update
        await self._update_logic(None)

    async def async_will_remove_from_hass(self):
        """Clean up."""
        if self._unsub_timer:
            self._unsub_timer()

    async def _update_logic(self, _):
        """Main logic wrapper."""
        self._recommendations = []
        
        # Calc Sub-Scores
        hw_score = await self._calc_hardware_score()
        sw_score = await self._calc_software_score()
        
        # Final Score Calculation
        final_score = min(hw_score, sw_score)
        
        self._score = max(0, min(100, final_score))
        
        # Update Attributes
        self._attr_extra_state_attributes = {
            "hardware_score": hw_score,
            "software_score": sw_score,
            "recommendations": self._recommendations,
            "storage_type": self._storage_type,
            "version": "2.2.0"
        }
        
        # Icon Logic
        if self._score >= 80:
            self._attr_icon = ICON_OK
        elif self._score >= 50:
            self._attr_icon = ICON_WARN
        else:
            self._attr_icon = ICON_CRIT
            
        self.async_write_ha_state()

    # --- PILLAR 1: HARDWARE (HYBRID: PSI + CPU) ---
    async def _calc_hardware_score(self):
        score = 100
        psi_available = False
        
        # A. PSI (Pressure Stall Information)
        psi_some_pressure = self.hass.states.get("sensor.system_monitor_processor_pressure")
        if psi_some_pressure and psi_some_pressure.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            psi_available = True
            try:
                psi_val = float(psi_some_pressure.state)
                if psi_val > 5.0:
                    score -= 15
                    self._recommendations.append(f"🔥 System Choking (PSI: {psi_val}). Processes are waiting.")
                elif psi_val > 2.0:
                    score -= 5
            except ValueError:
                pass

        # B. CPU Load
        cpu = self.hass.states.get("sensor.processor_use")
        if cpu and cpu.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            try:
                val = float(cpu.state)
                if psi_available:
                    # Hybrid Mode: High CPU is less critical if PSI is low
                    if val > 90:
                        score -= 5
                        self._recommendations.append(f"⚙️ High CPU ({val}%), but responsive.")
                else:
                    # Legacy Mode
                    if val > 85:
                        score -= 20
                        self._recommendations.append(f"🔥 High CPU Load: {val}%.")
            except ValueError:
                pass

        # C. Disk Usage
        disk_free = self.hass.states.get("sensor.disk_free_home")
        if disk_free and disk_free.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            try:
                free_gb = float(disk_free.state)
                # Stricter limits for SD Cards
                limit_critical = 5 if "SSD" in self._storage_type else 8
                limit_warn = 15 if "SSD" in self._storage_type else 20
                
                if free_gb < limit_critical:
                    score -= 50
                    self._recommendations.append(f"💾 [CRITICAL Storage]({self.LINK_STORAGE}): Only {free_gb}GB free!")
                elif free_gb < limit_warn:
                    score -= 10
                    self._recommendations.append(f"⚠️ [Low Storage]({self.LINK_STORAGE}): {free_gb}GB free.")
            except ValueError:
                pass
                
        return max(0, score)

    # --- PILLAR 2: SOFTWARE (Hygiene) ---
    async def _calc_software_score(self):
        score = 100
        
        # A. Database Size
        db_size = self.hass.states.get("sensor.recorder_db_size")
        if db_size and db_size.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            try:
                size_mb = float(db_size.state)
                if size_mb > 3000: # 3GB
                    score -= 15
                    self._recommendations.append(f"🗄️ [Huge Database]({self.LINK_DB}): {size_mb}MB.")
                elif size_mb > 1500:
                    score -= 5
                    self._recommendations.append(f"ℹ️ [Check Recorder]({self.LINK_RECORDER}): DB is {size_mb}MB.")
            except ValueError:
                pass

        # B. Zombies (Unavailable Entities)
        zombies = []
        for state in self.hass.states.async_all():
            if state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                if "update." in state.entity_id: 
                    continue
                zombies.append(state.entity_id)
        
        zombie_count = len(zombies)
        
        if zombie_count > 50:
            score -= 25
            self._recommendations.append(f"🧟 [Zombie Apocalypse]({self.LINK_ZOMBIES}): {zombie_count} unavailable entities.")
        elif zombie_count > 10:
            score -= 10
            self._recommendations.append(f"👻 [Clean Up]({self.LINK_ZOMBIES}): {zombie_count} unavailable entities.")

        return max(0, score)

    @property
    def native_value(self):
        """Return the state."""
        return self._score
