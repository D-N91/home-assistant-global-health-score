"""HAGHS Sensor - v2.2-dev Milestone 1 (Dynamic Update)."""
import logging
import math
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from .const import (
    CONF_CPU_SENSOR,
    CONF_RAM_SENSOR,
    CONF_DISK_SENSOR,
    CONF_DB_SENSOR,
    CONF_CORE_UPDATE_ENTITY,
    CONF_IGNORE_LABEL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HAGHS from a config entry."""
    # Get interval from entry data, fallback to default
    interval_min = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    
    # Apply the dynamic scan interval to this platform instance
    platform = entity_platform.async_get_current_platform()
    platform.scan_interval = timedelta(minutes=interval_min)
    
    _LOGGER.debug("HAGHS setup with update interval: %s minutes", interval_min)
    async_add_entities([HaghsSensor(hass, entry)], update_before_add=True)


class HaghsSensor(SensorEntity):
    """Representation of the HAGHS Sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = True  # Tell HA to call update() based on scan_interval

    def __init__(self, hass, entry):
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = f"{entry.entry_id}_score"
        self._attr_icon = "mdi:shield-check"
        self._attr_native_unit_of_measurement = " " 
        
        config = entry.data
        self.cpu_id = config.get(CONF_CPU_SENSOR)
        self.ram_id = config.get(CONF_RAM_SENSOR)
        self.disk_id = config.get(CONF_DISK_SENSOR)
        self.db_id = config.get(CONF_DB_SENSOR)
        self.core_update_id = config.get(CONF_CORE_UPDATE_ENTITY)
        self.ignore_label = config.get(CONF_IGNORE_LABEL)

    def update(self) -> None:
        """Fetch new state data and calculate score."""
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)

        # --- 1. PILLAR: HARDWARE (40%) ---
        cpu = self._get_float(self.cpu_id)
        p_cpu = 0
        if cpu <= 18: p_cpu = 0
        elif cpu <= 30: p_cpu = 15
        elif cpu <= 50: p_cpu = 40
        else: p_cpu = 80
        score_cpu = 100 - p_cpu

        ram = self._get_float(self.ram_id)
        score_ram = 100
        if ram >= 75: score_ram = max(0, 100 - (ram - 75) * 4)

        disk = self._get_float(self.disk_id)
        score_disk = 100
        if disk >= 85: score_disk = max(0, 100 - (disk - 85) * 6.6)

        hardware_final = (score_cpu + score_ram + score_disk) / 3

        # --- 2. PILLAR: APPLICATION (60%) ---
        
        # A. DYNAMIC ZOMBIE RATIO
        # Penalty calculation: $$P_{zombie} = \min(40, \frac{Zombies}{Total} \times 100)$$
        zombie_list = []
        total_eligible_entities = 0
        
        for state in self.hass.states.all():
            if state.domain not in ZOMBIE_DOMAINS: continue
            total_eligible_entities += 1
            
            if state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                entity_id = state.entity_id
                if "integration_health" in entity_id: continue

                is_ignored = self._is_entity_ignored(entity_id, ent_reg, dev_reg)
                if not is_ignored: zombie_list.append(entity_id)

        zombie_count = len(zombie_list)
        if total_eligible_entities > 0:
            zombie_ratio = (zombie_count / total_eligible_entities)
            p_zombie = min(40, zombie_ratio * 100)
        else:
            p_zombie = 0

        # B. CORE STABILITY CHECK
        p_core_stability = 0
        core_warnings = []
        for component in ["recorder", "history"]:
            if component not in self.hass.config.components:
                p_core_stability += 20
                core_warnings.append(f"CRITICAL: {component.capitalize()} missing!")

        # C. UPDATES (WITH IGNORE FILTER)
        update_count = 0
        for state in self.hass.states.all():
            if state.domain == "update" and state.state == "on":
                if not self._is_entity_ignored(state.entity_id, ent_reg, dev_reg):
                    update_count += 1
        
        p_updates = min(30, update_count * 5)

        # D. MAINTENANCE (DB)
        db_mb = self._get_float(self.db_id)
        p_db = 0 if db_mb < 1500 else (10 if db_mb < 3000 else 30)

        # FINAL CALC
        app_final = max(0, 100 - p_zombie - p_core_stability - p_updates - p_db)
        global_score = math.floor((hardware_final * 0.4) + (app_final * 0.6))
        self._attr_native_value = int(global_score)

        # --- ATTRIBUTES ---
        advice = core_warnings
        if p_cpu > 0: advice.append(f"⚡ CPU: High load ({cpu:.1f}%).")
        if disk >= 85: advice.append(f"⚠️ Disk: Critical space ({disk:.1f}%).")
        if p_zombie > 10: advice.append(f"🧟 Hygiene: High Zombie Ratio.")
        if update_count > 0: advice.append(f"📦 Updates: {update_count} pending.")

        self._attr_extra_state_attributes = {
            "hardware_score": int(hardware_final),
            "application_score": int(app_final),
            "zombie_ratio": f"{round((zombie_count / max(1, total_eligible_entities)) * 100, 1)}%",
            "zombie_entities": ", ".join(zombie_list[:10]) + ("..." if zombie_count > 10 else ""),
            "recommendations": "\n".join(advice) if advice else "✅ System Health Excellent"
        }

    def _is_entity_ignored(self, entity_id, ent_reg, dev_reg):
        """Check if an entity or its device has the ignore label."""
        entity_entry = ent_reg.async_get(entity_id)
        if not entity_entry: return False
        if self.ignore_label in entity_entry.labels: return True
        if entity_entry.device_id:
            device_entry = dev_reg.async_get(entity_entry.device_id)
            if device_entry and self.ignore_label in device_entry.labels: return True
        return False

    def _get_float(self, entity_id):
        if not entity_id: return 0.0
        state = self.hass.states.get(entity_id)
        if not state or state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]: return 0.0
        try: return float(state.state)
        except ValueError: return 0.0
