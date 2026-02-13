"""Constants for the HAGHS integration."""

DOMAIN = "haghs"
VERSION = "2.2.0"

# Configuration Keys
CONF_SENSORS = "sensors"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_STORAGE_TYPE = "storage_type"
CONF_LOG_FILE = "log_file"
CONF_IGNORE_LABEL = "haghs_ignore"

# Defaults
DEFAULT_NAME = "System HA Global Health Score"
DEFAULT_UPDATE_INTERVAL = 5  # Minutes
DEFAULT_STORAGE_TYPE = "SSD/NVMe"

# Storage Types for Dropdown
STORAGE_TYPES = [
    "SD Card",
    "SSD/NVMe",
    "HDD",
    "Virtual/Container"
]

# Scoring Constants
SCORE_PERFECT = 100
DEDUCTION_CRITICAL_DISK = 50
DEDUCTION_DB_SIZE = 20
DEDUCTION_ZOMBIES_MAX = 20
DEDUCTION_VERSION_LAG = 15
DEDUCTION_UNSUPPORTED = 100 # Spook/Unsupported logic
