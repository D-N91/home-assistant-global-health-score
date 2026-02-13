"""Sensor platform for HAGHS v2.2."""
import logging
import os
from datetime import timedelta, datetime

from homeassistant.components import recorder
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    STATE_ON,
)
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    CONF_STORAGE_TYPE,
    CONF_LOG_FILE,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)

ICON_HEALTHY = "mdi:heart-pulse"
ICON_WARNING = "mdi:alert-circle"
ICON_CRITICAL = "mdi:hospital-box"

# My Home Assistant Redirect Links
LINK_UPDATES = "https://my.home-assistant.io/redirect/updates/"
LINK_LOGS = "https://my.home-assistant.io/redirect/logs/"
LINK_STORAGE = "https://my.home-assistant.io/redirect/system_health/"
LINK_GENERIC = "https://www.home-assistant.io/docs/"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the HAGHS sensor."""
    async_add_entities([HaghsSensor(hass, config_entry)], True)


class HaghsSensor(SensorEntity):
    """Representation of the Global Health Score Sensor."""

    def __init__(self, hass, config_entry):
        """Initialize the sensor."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = f"{config_entry.entry_id}_score"
        
        # Load Config & Defaults
        self._storage_type = config_entry.data.get(CONF_STORAGE_TYPE, "SSD/NVMe")
        self._update_interval = config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        self._log_file_path = config_entry.data.get(CONF_LOG_FILE)

        self._state = None
        self._attributes = {}
        self._recommendations = []

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        if self._config_entry.options:
            self._update_from_options()
        
        self.async_on_remove(self._config_entry.add_update_listener(self.async_reload_entry))
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self.async_update_sensor, timedelta(minutes=self._update_interval)
            )
        )
        # Initial Update
        await self.async_update_sensor()

    async def async_reload_entry(self, hass, entry):
        """Reload options."""
        self._update_from_options()
        await self.async_update_sensor()

    def _update_from_options(self):
        """Update local vars from options flow."""
        self._storage_type = self._config_entry.options.get(CONF_STORAGE_TYPE, self._config_entry.data.get(CONF_STORAGE_TYPE))
        self._update_interval = self._config_entry.options.get(CONF_UPDATE_INTERVAL, self._config_entry.data.get(CONF_UPDATE_INTERVAL))
        self._log_file_path = self._config_entry.options.get(CONF_LOG_FILE, self._config_entry.data.get(CONF_LOG_FILE))

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def icon(self):
        if self._state is None or self._state >= 90:
            return ICON_HEALTHY
        if self._state >= 75:
            return ICON_WARNING
        return ICON_CRITICAL

    async def async_update_sensor(self, now=None):
        """Main Logic Loop."""
        self._recommendations = []
        
        # 1. Hardware Pillar (PSI, Storage Type Logic)
        hw_score = await self._calc_hardware_score()
        
        # 2. Application Pillar (Updates, Recorder, Zombies, DB)
        app_score = await self._calc_app_score()

        # Global Formula
        global_score = int((hw_score * 0.4) + (app_score * 0.6))
        
        self._state = global_score
        
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
        
        # A. PSI Logic
        psi_some_pressure = self.hass.states.get("sensor.system_monitor_processor_pressure")
        if psi_some_pressure and psi_some_pressure.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            try:
                psi_val = float(psi_some_pressure.state)
                if psi_val > 5.0:
                    score -= 20
                    self._recommendations.append(f"🔥 System Choking (PSI: {psi_val}). Hardware Limit reached.")
            except ValueError:
                pass
        else:
            # Fallback CPU
            cpu = self.hass.states.get("sensor.processor_use")
            if cpu and cpu.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                try:
                    val = float(cpu.state)
                    if val > 85:
                        score -= 20
                        self._recommendations.append(f"🔥 High CPU Load: {val}%.")
                except ValueError:
                    pass

        # B. Disk Usage (Absolute Thresholds + Storage Type Logic)
        disk_free = self.hass.states.get("sensor.disk_free_home")
        if disk_free and disk_free.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            try:
                free_gb = float(disk_free.state)
                limit_critical = 5 if "SSD" in self._storage_type else 8
                limit_warn = 15 if "SSD" in self._storage_type else 20
                
                if free_gb < limit_critical:
                    score -= 50
                    self._recommendations.append(f"💾 [CRITICAL Storage]({LINK_STORAGE}): Only {free_gb}GB free!")
                elif free_gb < limit_warn:
                    score -= 10
                    self._recommendations.append(f"⚠️ [Low Storage]({LINK_STORAGE}): {free_gb}GB free.")
            except ValueError:
                pass
                
        return max(0, score)

    # --- PILLAR 2: APPLICATION ---
    async def _calc_app_score(self):
        score = 100
        
        # Helper: Get Total Entities for Dynamic Calc
        all_states = self.hass.states.async_all()
        total_entities = len(all_states)
        self._attributes["total_entities"] = total_entities

        # A. Dynamic Database Limit (The Formula)
        # Limit = 1000MB + (Entities * 2.5MB)
        base_limit_mb = 1000 + (total_entities * 2.5)
        
        # Hardware Caps (Safety Net)
        if "SSD" in self._storage_type:
            # Pro User: Cap at 8GB (8000MB)
            final_limit_warn = min(base_limit_mb, 8000)
        else:
            # SD Card: Cap at 2.5GB (2500MB) to prevent wear-out
            final_limit_warn = min(base_limit_mb, 2500)
            
        final_limit_crit = final_limit_warn * 1.5 # Critical is 50% above warning

        db_size_mb = await self._get_database_size()
        if db_size_mb:
            self._attributes["db_size_mb"] = round(db_size_mb, 2)
            self._attributes["db_limit_dynamic"] = round(final_limit_warn, 2)
            
            if db_size_mb > final_limit_crit:
                score -= 20
                self._recommendations.append(f"🗄️ Database Critical (>{round(final_limit_crit)}MB). [Purge now]({LINK_GENERIC}).")
            elif db_size_mb > final_limit_warn:
                score -= 5
                self._recommendations.append(f"Database large (>{round(final_limit_warn)}MB). Check recorder.")
        else:
             self._attributes["db_size_mb"] = "Unknown"

        # B. Recorder Audit
        try:
            instance = recorder.get_instance(self.hass)
            if hasattr(instance, 'commit_interval'):
                if instance.commit_interval < 30 and "SD" in self._storage_type:
                    self._recommendations.append("⚙️ Recorder: [Increase commit_interval](https://www.home-assistant.io/integrations/recorder/#commit_interval) to save your SD Card.")
                    score -= 2
            if hasattr(instance, 'keep_days'):
                 if instance.keep_days > 30:
                     score -= 5
                     self._recommendations.append(f"⚙️ Recorder: keep_days is {instance.keep_days}. [Lower it]({LINK_GENERIC}).")
        except Exception:
            pass 

        # C. Updates
        pending_updates = []
        for state in all_states:
            if state.domain == "update" and state.state == STATE_ON:
                if "haghs_ignore" in state.entity_id or state.attributes.get("skipped") is True:
                    continue
                pending_updates.append(state.attributes.get("friendly_name", state.entity_id))

        if pending_updates:
            count = len(pending_updates)
            self._attributes["pending_updates"] = pending_updates
            self._attributes["update_count"] = count
            score -= min(15, count * 2) 
            if count > 0:
                self._recommendations.append(f"📦 [{count} Updates pending]({LINK_UPDATES}) (See attributes).")

        # D. Log File
        if self._log_file_path:
            log_size = await self._get_file_size(self._log_file_path)
            if log_size and log_size > 50:
                score -= 5
                self._recommendations.append(f"📜 [Log file]({LINK_LOGS}) > 50MB.")

        # E. Zombie Ratio (New Logic)
        zombies = []
        for state in all_states:
            if state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                if "haghs_ignore" in state.entity_id:
                     continue
                zombies.append(state.entity_id)
        
        zombie_count = len(zombies)
        self._attributes["zombie_entities"] = zombies[:20] 
        self._attributes["zombie_count"] = zombie_count
        
        # Calculate Ratio
        if total_entities > 0:
            zombie_ratio = (zombie_count / total_entities) * 100
            self._attributes["zombie_ratio_percent"] = round(zombie_ratio, 2)
            
            if zombie_count > 0:
                # Dynamic Scoring: 2 points penalty per 1% dead entities
                # Example: 5% dead = -10 points. 10% dead = -20 points.
                # Cap at 25 points max deduction
                deduction = min(25, int(zombie_ratio * 2))
                # Ensure at least 1 point deduction if zombies exist
                deduction = max(1, deduction)
                
                score -= deduction
                
                if zombie_ratio > 5:
                    self._recommendations.append(f"🧟 High Zombie Ratio ({round(zombie_ratio, 1)}%). System unstable.")

        return max(0, score)

    async def _get_database_size(self):
        try:
            instance = recorder.get_instance(self.hass)
            db_url = instance.db_url
            if "sqlite://" in db_url:
                db_path = self.hass.config.path("home-assistant_v2.db")
                return await self._get_file_size(db_path)
            return None 
        except Exception:
            return None

    async def _get_file_size(self, path):
        def _size():
            if os.path.exists(path):
                return os.path.getsize(path) / 1024 / 1024
            return None
        return await self.hass.async_add_executor_job(_size)
