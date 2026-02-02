"""Constants for the HAGHS integration."""

DOMAIN = "haghs"
DEFAULT_NAME = "HAGHS Advisor"

# Technische Keys für die Speicherung
CONF_CPU_SENSOR = "cpu_sensor"
CONF_RAM_SENSOR = "ram_sensor"
CONF_DISK_SENSOR = "disk_sensor"
CONF_DB_SENSOR = "db_sensor"
CONF_CORE_UPDATE_ENTITY = "core_update_entity"
CONF_IGNORE_LABEL = "ignore_label"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_LATENCY_SENSOR = "latency_sensor"
# NEU für v2.2:
CONF_UPDATE_INTERVAL = "update_interval"
CONF_STORAGE_TYPE = "storage_type"
STORAGE_TYPE_SD = "sd_card"
STORAGE_TYPE_SSD = "ssd_nvme"

# Standardwerte
DEFAULT_UPDATE_INTERVAL = 5
