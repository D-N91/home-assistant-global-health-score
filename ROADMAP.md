# HAGHS Roadmap

This document outlines planned features and improvements for the Home Assistant Global Health Score.

## Planned

### Hardware Health Expansion: CPU Temperature & Power Supply Status (#21)

Enhance the hardware score with two new optional metrics:

- **CPU Temperature** — Detect thermal stress, throttling risks, and poor airflow. Users can define a target and max-safe temperature via config flow. The score decreases gradually as temperature approaches the limit.
- **Power Supply Status** — Detect under-voltage conditions on Raspberry Pi devices. A `Problem` state reduces the health score to reflect real hardware instability.

Both metrics remain optional to support diverse hardware platforms (RPi, x86, mini PCs).

---

*Last updated: 2026-03-31*
