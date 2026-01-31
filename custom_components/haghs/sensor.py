"""HAGHS Sensor - v2.2-dev Milestone 2 (Grouping & Bulk Helper)."""
import logging
import math
from datetime import timedelta
from collections import defaultdict

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr, entity_registry as er, entity_platform
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

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
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    interval_min = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    platform = entity_platform.async_get_current_platform()
    platform.scan_interval = timedelta(minutes=interval_min)
    async_add_entities([HaghsSensor(hass, entry)], update_before_add=True)

class HaghsSensor(SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = True

    def __init__(self, hass, entry):
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
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)

        # Groups for categorized advice
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
        if p_cpu > 0: advice_groups["Hardware"].append(f"CPU load is high ({cpu:.1f}%)")

        ram = self._get_float(self.ram_id)
        score_ram = 100
        if ram >= 75: 
            score_ram = max(0, 100 - (ram - 75) * 4)
            advice_groups["Hardware"].append(f"RAM usage is high ({ram:.1f}%)")

        disk = self._get_float(self.disk_id)
        score_disk = 100
        if disk >= 85: 
            score_disk = max(0, 100 - (disk - 85) * 6.6)
            advice_groups["Critical"].append(f"Disk space critical ({disk:.1f}%)")

        hardware_final = (100 - p_cpu + score_ram + score_disk) / 3

        # --- 2. PILLAR: APPLICATION (60%) ---
        
        # A. DYNAMIC ZOMBIE RATIO & GROUPING
        zombies_by_domain = defaultdict(list)
        zombie_list_full = []
        total_eligible = 0
        
        for state in self.hass.states.all():
            if state.domain not in ["sensor", "binary_sensor", "switch", "light", "fan", "climate", "media_player", "vacuum", "camera"]: continue
            total_eligible += 1
            if state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                if "integration_health" in state.entity_id: continue
                if not self._is_entity_ignored(state.entity_id, ent_reg, dev_reg):
                    zombies_by_domain[state.domain].append(state.entity_id.split('.')[-1])
                    zombie_list_full.append(state.entity_id)

        zombie_count = len(zombie_list_full)
        p_zombie = min(40, (zombie_count / max(1, total_eligible)) * 100)
        
        if zombie_count > 0:
            zombie_summary = ", ".join([f"{count} {dom}" for dom, count in {d: len(z) for d, z in zombies_by_domain.items()}.items()])
            advice_groups["Hygiene"].append(f"Found {zombie_count} zombies: {zombie_summary}")

        # B. CORE STABILITY
        p_core = 0
        for comp in ["recorder", "history"]:
            if comp not in self.hass.config.components:
                p_core += 20
                advice_groups["Critical"].append(f"System core '{comp}' is missing!")

        # C. UPDATES
        update_count = 0
        for state in self.hass.states.all():
            if state.domain == "update" and state.state == "on":
                if not self._is_entity_ignored(state.entity_id, ent_reg, dev_reg):
                    update_count += 1
        if update_count > 0:
            advice_groups["Maintenance"].append(f"{update_count} updates pending")

        # D. DATABASE
        db_mb = self._get_float(self.db_id)
        p_db = 0 if db_mb < 1500 else (10 if db_mb < 3000 else 30)
        if p_db > 0: advice_groups["Maintenance"].append(f"Database size: {db_mb/1000:.1f} GB")

        # FINAL CALC
        app_final = max(0, 100 - p_zombie - p_core - (min(30, update_count * 5)) - p_db)
        self._attr_native_value = int(math.floor((hardware_final * 0.4) + (app_final * 0.6)))

        # Format Recommendations
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
