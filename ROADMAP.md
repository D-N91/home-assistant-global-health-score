# HAGHS Roadmap

This document outlines planned features and improvements for the Home Assistant Global Health Score.

## In Progress (dev branch)

### Power Supply Status Detection (#21)

Auto-detect under-voltage conditions on Raspberry Pi devices via `binary_sensor.rpi_power_status`. A `Problem` state applies a flat 20-point penalty to the hardware score. No configuration needed — the check is skipped automatically on non-RPi hardware.

## Planned

### PSI-Aware Recommendation Text

**Problem:** Two separate users confused PSI stall time with classic CPU utilization because the Advisor message `"CPU load is impacting score (6.5%)"` gives no indication that 6.5% refers to PSI stall time, not utilization percentage. Users who see 38% in System Monitor and 6.5% in the Advisor assume HAGHS is reacting to the wrong value.

**Solution:** Split `REC_CPU_LOAD` in `_build_recommendations` into two context-aware variants:
- PSI active: `"PSI CPU stall time is impacting score (X%)"` — makes the metric type explicit
- Classic sensor: `"CPU utilization is impacting score (X%)"` — unchanged behavior

Same pattern should be applied to the RAM and I/O recommendation strings for consistency.

**Scope:** Backend only (`__init__.py` + `const.py` + `strings.json`). No scoring logic changes, no breaking changes to sensor attributes.

---

## Declined

### CPU Temperature Monitoring (#21)

**Status:** Will not be implemented.

**Reasoning:** CPU temperature is a predictive hardware metric, not a current health indicator. If thermal throttling occurs, it already surfaces through elevated PSI stall values, which HAGHS captures. Adding temperature as a scoring component would dilute the existing hardware score without adding actionable health information. The required user configuration (sensor selection, threshold definition per hardware platform) conflicts with the pragmatism principle.

---

*Last updated: 2026-04-09*
