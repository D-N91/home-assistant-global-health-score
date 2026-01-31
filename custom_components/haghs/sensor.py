"""HAGHS Sensor - v2.2-dev Final."""
import logging
import math
from datetime import timedelta
from collections import defaultdict

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import (
    device_registry as dr, 
    entity_registry as er, 
    entity_platform
)
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from .const import (
    CONF_CPU_SENSOR,
    CONF_RAM_SENSOR,
    CONF_DISK_SENSOR,
    CONF_DB_SENSOR,
    CONF_CORE_UPDATE_ENTITY,
    CONF_IGNORE_LABEL,
    CONF_UPDATE_INTERVAL,
    CONF_TEMP_SENSOR,
    CONF_LATENCY_SENSOR,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up HAGHS from a config entry."""
    interval_min = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    
    # Apply dynamic scan interval
    current_platform = entity_platform.async_get_current_platform()
    current_platform.scan_interval = timedelta(minutes=interval_min)
    
    async_add_entities([HaghsSensor(hass, entry)], update_before_add=True)

class HaghsSensor(SensorEntity):
    """Representation of the HAGHS Sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = True

    def __init__(self, hass, entry):
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = f"{entry.entry_id}_score"
        self._attr_icon = "mdi:shield-check"
        self._attr_native_unit_of_measurement = " " 
        
        # Load all IDs consistently from config entry
        config = entry.data
        self.cpu_id = config.get(CONF_CPU_SENSOR)
        self.ram_id = config.get(CONF_RAM_SENSOR)
        self.disk_id = config.get(CONF_DISK_SENSOR)
        self.db_id = config.get(CONF_DB_SENSOR)
        self.core_update_id = config.get(CONF_CORE_UPDATE_ENTITY)
        self.ignore_label = config.get(CONF_IGNORE_LABEL)
        self.temp_id = config.get(CONF_TEMP_SENSOR)
        self.latency_id = config.get(CONF_LATENCY_SENSOR)

    def update(self) -> None:
        """Fetch new data and calculate the health score."""
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)

        advice_groups = {
            "Critical": [],
            "Hardware": [],
            "Maintenance": [],
            "Hygiene": []
        }

        # --- 1. PILLAR: HARDWARE (40%) ---
        cpu = self._get_float(self.cpu_id)
        p_cpu = 0
        if cpu <= 18: p_cpu = 0
        elif cpu <= 30: p_cpu = 15
        elif cpu <= 50: p_cpu = 40
        else: p_cpu = 80
        if p_cpu > 0: advice_groups["Hardware"].append(f"CPU load high ({cpu:.1f}%)")

        ram = self._get_float(self.ram_id)
        score_ram = 100
        if ram >= 75: 
            score_ram = max(0, 100 - (ram - 75) * 4)
            advice_groups["Hardware"].append(f"RAM usage high ({ram:.1f}%)")

        disk = self._get_float(self.disk_id)
        score_disk = 100
        if disk >= 85: 
            score_disk = max(0, 100 - (disk - 85) * 6.6)
            advice_groups["Critical"].append(f"Disk space critical ({disk:.1f}%)")

        # Dynamic Hardware values (weighted calculation)
        hw_values = [100 - p_cpu, score_ram, score_disk]
        
        if self.temp_id:
            temp = self._get_float(self.temp_id)
            p_temp = 0
            if temp > 65:
                p_temp = min(50, (temp - 65) * 2)
                if p_temp > 10: advice_groups["Hardware"].append(f"CPU temp high ({temp:.1f}°C)")
            hw_values.append(100 - p_temp)

        if self.latency_id:
            latency = self._get_float(self.latency_id)
            p_latency = 0
            if latency > 100:
                p_latency = min(40, (latency - 100) / 5)
                if p_latency > 10: advice_groups["Critical"].append(f"Storage latency high ({latency:.0f}ms)")
            hw_values.append(100 - p_latency)

        hardware_final = sum(hw_values) / len(hw_values)

        # --- 2. PILLAR: APPLICATION (60%) ---
        zombie_list_full = []
        total_eligible = 0
        zombies_by_domain = defaultdict(list)
        
        zombie_domains = ["sensor", "binary_sensor", "switch", "light", "fan", "climate", "media_player", "vacuum", "camera"]
        
        for state in self.hass.states.all():
            if state.domain not in zombie_domains: continue
            total_eligible += 1
            if state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                if "integration_health" in state.entity_id: continue
                if not self._is_entity_ignored(state.entity_id, ent_reg, dev_reg):
                    zombies_by_domain[state.domain].append(state.entity_id)
                    zombie_list_full.append(state.entity_id)

        zombie_count = len(zombie_list_full)
        p_zombie = min(40, (zombie_count / max(1, total_eligible)) * 100)
        if zombie_count > 0:
            dom_summary = ", ".join([f"{len(ids)} {dom}" for dom, ids in zombies_by_domain.items()])
            advice_groups["Hygiene"].append(f"Zombies: {dom_summary}")

        # Core Stability Check
        p_core = 0
        for comp in ["recorder", "history"]:
            if comp not in self.hass.config.components:
                p_core += 20
                advice_groups["Critical"].append(f"Core '{comp}' not loaded")

        # Updates Check
        update_count = 0
        for state in self.hass.states.all():
            if state.domain == "update" and state.state == "on":
                if not self._is_entity_ignored(state.entity_id, ent_reg, dev_reg):
                    update_count += 1
        
        db_mb = self._get_float(self.db_id)
        p_db = 0 if db_mb < 1500 else (10 if db_mb < 3000 else 30)

        app_final = max(0, 100 - p_zombie - p_core - (min(30, update_count * 5)) - p_db)
        
        # Calculate Global Score
        global_score = math.floor((hardware_final * 0.4) + (app_final * 0.6))
        self._attr_native_value = int(global_score)

        # Format Recommendations Attribute
        formatted_advice = []
        for cat, items in advice_groups.items():
            if items:
                formatted_advice.append(f"[{cat}]")
                formatted_advice.extend([f" - {item}" for item in items])

        self._attr_extra_state_attributes = {
            "hardware_score": int(hardware_final),
            "application_score": int(app_final),
            "zombie_ratio": f"{round((zombie_count / max(1, total_eligible)) * 100, 1)}%",
            "zombie_bulk_list": ", ".join(zombie_list_full),
            "recommendations": "\n".join(formatted_advice) if formatted_advice else "✅ System Healthy"
        }

    def _is_entity_ignored(self, entity_id, ent_reg, dev_reg):
        """Check if entity or device has the ignore label."""
        entity_entry = ent_reg.async_get(entity_id)
        if not entity_entry: return False
        if self.ignore_label in entity_entry.labels: return True
        if entity_entry.device_id:
            device_entry = dev_reg.async_get(entity_entry.device_id)
            if device_entry and self.ignore_label in device_entry.labels: return True
        return False

    def _get_float(self, entity_id):
        """Helper to get state as float."""
        if not entity_id: return 0.0
        state = self.hass.states.get(entity_id)
        if not state or state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]: return 0.0
        try: return float(state.state)
        except ValueError: return 0.0
