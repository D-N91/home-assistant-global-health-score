"""Sensor platform for HAGHS v2.2."""
import logging
import os
import shutil
from datetime import timedelta, datetime

from homeassistant.components import recorder
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    CONF_STORAGE_TYPE,
    CONF_LOG_FILE,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)

# Icons
ICON_HEALTHY = "mdi:heart-pulse"
ICON_WARNING = "mdi:alert-circle"
ICON_CRITICAL = "mdi:hospital-box"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the HAGHS sensor from a config entry."""
    async_add_entities([HaghsSensor(hass, config_entry)], True)


class HaghsSensor(SensorEntity):
    """Representation of the Global Health Score Sensor."""

    def __init__(self, hass, config_entry):
        """Initialize the sensor."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = f"{config_entry.entry_id}_score"
        
        # Load Config
        self._storage_type = config_entry.data.get(CONF_STORAGE_TYPE)
        self._update_interval = config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        self._log_file_path = config_entry.data.get(CONF_LOG_FILE)

        # State vars
        self._state = None
        self._attributes = {}
        self._recommendations = []

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        # Use config entry options if available (OptionsFlow support)
        if self._config_entry.options:
            self._update_from_options()
        
        # Listener for Config Updates
        self.async_on_remove(self._config_entry.add_update_listener(self.async_reload_entry))

        # Schedule updates
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self.async_update_sensor, timedelta(minutes=self._update_interval)
            )
        )
        # Initial update
        await self.async_update_sensor()

    async def async_reload_entry(self, hass, entry):
        """Reload when options change."""
        self._update_from_options()
        await self.async_update_sensor()

    def _update_from_options(self):
        """Update local vars from options."""
        self._storage_type = self._config_entry.options.get(CONF_STORAGE_TYPE, self._config_entry.data.get(CONF_STORAGE_TYPE))
        self._update_interval = self._config_entry.options.get(CONF_UPDATE_INTERVAL, self._config_entry.data.get(CONF_UPDATE_INTERVAL))
        self._log_file_path = self._config_entry.options.get(CONF_LOG_FILE, self._config_entry.data.get(CONF_LOG_FILE))

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Return dynamic icon."""
        if self._state is None:
            return ICON_HEALTHY
        if self._state >= 90:
            return ICON_HEALTHY
        if self._state >= 75:
            return ICON_WARNING
        return ICON_CRITICAL

    async def async_update_sensor(self, now=None):
        """Main Update Logic."""
        self._recommendations = []
        
        # 1. Hardware Score (40%)
        hw_score = await self._calc_hardware_score()
        
        # 2. Application Score (60%)
        app_score = await self._calc_app_score()

        # Global Formula (v2.2)
        # Using Floor to be strict
        global_score = int((hw_score * 0.4) + (app_score * 0.6))
        
        self._state = global_score
        
        # Update Attributes
        self._attributes = {
            "score_hardware": hw_score,
            "score_application": app_score,
            "recommendations": self._recommendations,
            "storage_type": self._storage_type,
            "last_updated": datetime.now().isoformat(),
        }
        
        self.async_write_ha_state()

    # --- PILLAR 1: HARDWARE ---
    async def _calc_hardware_score(self):
        score = 100
        # NOTE: PSI Integration to follow in next iteration once SystemMonitor exposes it natively.
        # Fallback to Load/CPU for now.
        
        # CPU / Load Check
        cpu_load = self.hass.states.get("sensor.processor_use")
        if cpu_load and cpu_load.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            try:
                val = float(cpu_load.state)
                if val > 80:
                    score -= 20
                    self._recommendations.append(f"🔥 Critical CPU Load: {val}%")
                elif val > 40:
                    score -= 5
            except ValueError:
                pass
        
        # Disk Check (Absolute Logic)
        # Try to find common disk sensors or use psutil fallback if we were allowed (we stick to HA sensors for safety)
        # Looking for 'sensor.disk_free_home' (standard systemmonitor)
        disk_free = self.hass.states.get("sensor.disk_free_home")
        if disk_free and disk_free.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            try:
                free_gb = float(disk_free.state)
                # Logic: Less than 10GB is scary for DB backups
                if free_gb < 5:
                    score -= 50
                    self._recommendations.append(f"💾 CRITICAL Storage: Only {free_gb}GB free!")
                elif free_gb < 15:
                    score -= 10
                    self._recommendations.append(f"⚠️ Low Storage: {free_gb}GB free.")
            except ValueError:
                pass
                
        return max(0, score)

    # --- PILLAR 2: APPLICATION ---
    async def _calc_app_score(self):
        score = 100
        
        # A. Database Size (Zero-YAML)
        db_size_mb = await self._get_database_size()
        if db_size_mb:
            self._attributes["db_size_mb"] = round(db_size_mb, 2)
            # Thresholds
            if db_size_mb > 2500: # 2.5 GB
                score -= 20
                self._recommendations.append("🗄️ Database Critical (>2.5GB). Purge recommended.")
            elif db_size_mb > 1000: # 1 GB
                score -= 5
                self._recommendations.append("Database large (>1GB). Check recorder settings.")
        else:
             self._attributes["db_size_mb"] = "Unknown"

        # B. Log File (Optional)
        if self._log_file_path:
            log_size = await self._get_file_size(self._log_file_path)
            if log_size and log_size > 50: # 50 MB
                score -= 5
                self._recommendations.append(f"📜 Log file is huge ({log_size}MB). Check for errors.")

        # C. Zombies (Capped at 20)
        zombies = []
        for state in self.hass.states.async_all():
            if state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                # Check for Ignore Label
                # (Assuming labels are available on entity - needs HA 2024.4+)
                # Basic check logic
                if "haghs_ignore" in state.entity_id: # Quick implementation
                     continue
                zombies.append(state.entity_id)
        
        zombie_count = len(zombies)
        # Cap the list for attributes to prevent bloating state machine
        self._attributes["zombie_entities"] = zombies[:20] 
        self._attributes["zombie_count"] = zombie_count
        
        if zombie_count > 0:
            deduction = min(20, zombie_count * 1) # 1 point per zombie, max 20
            score -= deduction
            if zombie_count > 20:
                 self._recommendations.append(f"🧟 {zombie_count} Zombies detected (List capped).")

        return max(0, score)

    # --- HELPERS ---
    async def _get_database_size(self):
        """Get DB size without YAML config."""
        try:
            instance = recorder.get_instance(self.hass)
            db_url = instance.db_url
            
            # Case 1: SQLite (Local File)
            if "sqlite://" in db_url:
                # Usually 'sqlite:////config/home-assistant_v2.db'
                # We extract the path or assume default
                db_path = self.hass.config.path("home-assistant_v2.db")
                return await self._get_file_size(db_path)
            
            # Case 2: MariaDB / MySQL (Future: Execute Query)
            # For v2.2 initial, we skip SQL query to avoid blocking executor without detailed testing
            return None
            
        except Exception as e:
            _LOGGER.warning(f"Could not determine DB size: {e}")
            return None

    async def _get_file_size(self, path):
        """Async file size check."""
        def _size():
            if os.path.exists(path):
                return os.path.getsize(path) / 1024 / 1024 # MB
            return None
        return await self.hass.async_add_executor_job(_size)
