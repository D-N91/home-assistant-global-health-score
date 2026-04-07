"""The HAGHS integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    label_registry as lr,
)

from .const import (
    CONF_IGNORE_LABEL,
    DOMAIN,
    VersionInformation,
)
from .coordinator import HaghsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HAGHS from a config entry."""
    coordinator = HaghsDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    entry_version = VersionInformation(major=entry.version, minor=entry.minor_version)

    _LOGGER.info("Migrating configuration from version %s", entry_version)

    label_change_version = VersionInformation(major=3, minor=2)
    if entry_version <= label_change_version:
        if lr.DATA_REGISTRY not in hass.data:
            await lr.async_load(hass)

        label_registry = lr.async_get(hass)

        data = dict(entry.data)
        options = dict(entry.options)
        data_changed = _migrate_ignore_label_value(label_registry, data)
        options_changed = _migrate_ignore_label_value(label_registry, options)

        if data_changed or options_changed:
            _LOGGER.info("HAGHS: Migrated ignore label to label ID")

        hass.config_entries.async_update_entry(
            entry,
            data=data,
            options=options,
            version=label_change_version.major,
            minor_version=label_change_version.minor,
        )

    _LOGGER.info("Migration to version %s successful", entry_version)
    return True


def _migrate_ignore_label_value(
    label_registry: lr.LabelRegistry,
    config: dict[str, Any],
) -> bool:
    """Convert legacy text ignore label value into a label ID."""
    label_value = config.get(CONF_IGNORE_LABEL, None)

    if not label_value:
        return True

    if label := label_registry.async_get_label_by_name(label_value):
        config[CONF_IGNORE_LABEL] = label.label_id
        return True

    try:
        created = label_registry.async_create(label_value)
    except ValueError:
        # Handle races/case-normalization collisions.
        if label := label_registry.async_get_label_by_name(label_value):
            config[CONF_IGNORE_LABEL] = label.label_id
            return True
        _LOGGER.warning(
            "HAGHS: Could not migrate ignore label '%s', clearing the value",
            label_value,
        )
        config.pop(CONF_IGNORE_LABEL, None)
        return True

    config[CONF_IGNORE_LABEL] = created.label_id
    _LOGGER.debug(
        "HAGHS: Created label '%s' during migration (id=%s)",
        label_value,
        created.label_id,
    )
    return True
