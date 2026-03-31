# HAGHS Roadmap

This document outlines planned features and improvements for the Home Assistant Global Health Score.

## In Progress (dev branch)

### Power Supply Status Detection (#21)

Auto-detect under-voltage conditions on Raspberry Pi devices via `binary_sensor.rpi_power_status`. A `Problem` state applies a flat 20-point penalty to the hardware score. No configuration needed — the check is skipped automatically on non-RPi hardware.

## Declined

### CPU Temperature Monitoring (#21)

**Status:** Will not be implemented.

**Reasoning:** CPU temperature is a predictive hardware metric, not a current health indicator. If thermal throttling occurs, it already surfaces through elevated PSI stall values, which HAGHS captures. Adding temperature as a scoring component would dilute the existing hardware score without adding actionable health information. The required user configuration (sensor selection, threshold definition per hardware platform) conflicts with the pragmatism principle.

---

*Last updated: 2026-03-31*
