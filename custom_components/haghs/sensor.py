"""HAGHS Sensor - v2.2.0-dev Final."""
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
    CONF_STORAGE_TYPE,
    STORAGE_TYPE_SD,
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
        
        config = entry.data
        self.cpu_id = config.get(CONF_CPU_SENSOR)
        self.ram_id = config.get(CONF_RAM_SENSOR)
        self.disk_id = config.get(CONF_DISK_SENSOR)
        self.db_id = config.get(CONF_DB_SENSOR)
        self.core_update_id = config.get(CONF_CORE_UPDATE_ENTITY)
        self.ignore_label = config.get(CONF_IGNORE_LABEL)
        self.temp_id = config.get(CONF_TEMP_SENSOR)
        self.latency_id = config.get(CONF_LATENCY_SENSOR)
        self.storage_type = config.get(CONF_STORAGE_TYPE, STORAGE_TYPE_SD)

    def update(self) -> None:
        """Fetch data and calculate score."""
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
        if cpu > 18:
            p_cpu = 15 if cpu <= 30 else (40 if cpu <= 50 else 80)
            advice_groups["Hardware"].append(f"CPU load high ({cpu:.1f}%)")

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

        hw_values = [100 - p_cpu, score_ram, score_disk]
        
        if self.temp_id:
            temp = self._get_float(self.temp_id)
            p_temp = min(50, (temp - 65) * 2) if temp > 65 else 0
            if p_temp > 10: advice_groups["Hardware"].append(f"CPU temp high ({temp:.1f}°C)")
            hw_values.append(100 - p_temp)

        if self.latency_id:
            latency = self._get_float(self.latency_id)
            p_latency = min(40, (latency - 100) / 5) if latency > 100 else 0
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

        # Dynamic Zombie Ratio
        p_zombie = min(40, (len(zombie_list_full) / max(1, total_eligible)) * 100)
        if len(zombie_list_full) > 0:
            dom_summary = ", ".join([f"{len(ids)} {dom}" for dom, ids in zombies_by_domain.items()])
            advice_groups["Hygiene"].append(f"Zombies: {dom_summary}")

        # Core Check
        p_core = 0
        for comp in ["recorder", "history"]:
            if comp not in self.hass.config.components:
                p_core += 20
                advice_groups["Critical"].append(f"Core '{comp}' not loaded")

        # Updates
        update_count = sum(1 for state in self.hass.states.all() 
                          if state.domain == "update" and state.state == "on" 
                          and not self._is_entity_ignored(state.entity_id, ent_reg, dev_reg))
        
        # --- DYNAMIC DATABASE LOGIC ---
        db_mb = self._get_float(self.db_id)
        # 1000MB Base + 2.5MB per eligible entity
        calc_limit = 1000 + (total_eligible * 2.5)
        # Hardware Veto
        dyn_limit = min(2500, calc_limit) if self.storage_type == STORAGE_TYPE_SD else min(8000, calc_limit)
        
        p_db = min(30, math.floor((db_mb - dyn_limit) / 500) * 10) if db_mb > dyn_limit else 0
        if p_db > 0:
            s_mode = "SD Card (Strict)" if self.storage_type == STORAGE_TYPE_SD else "SSD (Relaxed)"
            advice_groups["Maintenance"].append(f"DB too large for {s_mode}: {db_mb/1000:.1f}GB")

        app_final = max(0, 100 - p_zombie - p_core - (min(30, update_count * 5)) - p_db)
        self._attr_native_value = int(math.floor((hardware_final * 0.4) + (app_final * 0.6)))

        # Final Formatting
        formatted_advice = []
        for cat, items in advice_groups.items():
            if items:
                formatted_advice.append(f"[{cat}]")
                formatted_advice.extend([f" - {item}" for item in items])

        self._attr_extra_state_attributes = {
            "hardware_score": int(hardware_final),
            "application_score": int(app_final),
            "zombie_ratio": f"{round((len(zombie_list_full) / max(1, total_eligible)) * 100, 1)}%",
            "zombie_bulk_list": ", ".join(zombie_list_full),
            "recommendations": "\n".join(formatted_advice) if formatted_advice else "✅ System Healthy"
        }

    def _is_entity_ignored(self, entity_id, ent_reg, dev_reg):
        entry = ent_reg.async_get(entity_id)
        if not entry: return False
        if self.ignore_label in entry.labels: return True
        if entry.device_id:
            d_entry = dev_reg.async_get(entry.device_id)
            if d_entry and self.ignore_label in d_entry.labels: return True
        return False

    def _get_float(self, eid):
        if not eid: return 0.0
        state = self.hass.states.get(eid)
        if not state or state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]: return 0.0
        try: return float(state.state)
        except ValueError: return 0.0
