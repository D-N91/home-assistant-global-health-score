## HAGHS: Home Assistant Global Health Score
**A Technical Specification for System Stability and Hygiene Standardized Monitoring.**

[![HAGHS Standard](https://img.shields.io/badge/HAGHS-Standard-blue?style=for-the-badge&logo=home-assistant&logoColor=white)](https://github.com/d-n91/home-assistant-global-health-score)
[![Release](https://img.shields.io/badge/Version-2.1.1-green?style=for-the-badge)](https://github.com/d-n91/home-assistant-global-health-score/releases)
 [![My HAGHS Score](https://img.shields.io/badge/HAGHS-86%20%2F%20100-brightgreen?style=for-the-badge&logo=home-assistant)](https://github.com/d-n91/home-assistant-global-health-score)
![AI-Powered](https://img.shields.io/badge/Developed%20with-AI-blue?style=for-the-badge&logo=google-gemini&logoColor=white)

## Abstract
As Home Assistant matures into a mission-critical Smart Home OS, the need for a unified stability metric becomes paramount. **HAGHS** is a logical framework designed to provide an objective **Health Index (0-100)**. It differentiates between transient hardware load and chronic maintenance neglect, providing users with a "North Star" for instance optimization.

---

## The HAGHS Standard (v2.1.1)

The index is calculated via a weighted average of two core pillars, prioritizing long-term software hygiene over temporary hardware fluctuations.

### The Global Formula

$$Score_{Global} = \lfloor (Score_{Hardware} \cdot 0.4) + (Score_{Application} \cdot 0.6) \rfloor$$

*Note: We use **Floor Rounding** (Integer) to ensure a "Perfect 100" is only achieved by truly optimized systems. Even a minor penalty will drop the score to 99.*

---

## Pillar 1: Hardware Performance (40%)

Evaluates the physical constraints of the host machine. It uses tiered penalties to filter out background noise while flagging genuine resource exhaustion.

* **CPU Load (Tiered):** Penalties start at **>10% usage** to ensure responsiveness.
* **Memory Pressure:** Deductions apply above **70% usage** to respect native Supervisor overhead.
* **Storage Integrity:** Critical deduction when disk usage exceeds **80%**, escalating as the system nears the 95% threshold.

---

## Pillar 2: Application Hygiene (60%)

Measures "maintenance debt"—the hidden factors that cause sluggishness, failed backups, and slow restarts.

* **Zombie Entities:** Monitors `unavailable` or `unknown` states (Capped at 20 pts).
* **Database Hygiene:** Penalizes `home-assistant_v2.db` growth (>1GB Warning / >2.5GB Critical).
* **Updates & Core Age:** Tracks pending updates and penalizes a "Core Version Lag" of >2 months.
* **Safety Net:** A static **30-point deduction** for stale backups.

---

## Configuration (The UI Way)

HAGHS is installed as a **HACS Custom Repository** and configured via a **Setup Mask (UI)**. 

### 1. Prerequisites (Prepare your Sensors)

**A. System Monitor:**
Install the **System Monitor** integration. Ensure these specific sensors are **enabled**:
* `sensor.processor_use` (Percentage %)
* `sensor.memory_use_percent` (Percentage %)
* `sensor.disk_use_percent_home` (Percentage %)

**B. Database Sensor (SQLite / Standard):**
To allow Home Assistant to see its own database size, add this to your `configuration.yaml` and restart:

```yaml
homeassistant:
  allowlist_external_dirs:
    - "/config"
```

**After the restart:**
1.  Go to **Settings > Integrations > Add Integration**.
2.  Search for **File Size** and set the path to: `/config/home-assistant_v2.db`.

*Note: For MariaDB/Postgres, create a SQL sensor that returns the size in MB.*

### 2. Installation & Setup
1.  Add this repo to **HACS** (Custom Repository, Category: Integration).
2.  Download and **Restart Home Assistant**.
3.  Go to **Settings > Integrations > Add Integration** and search for **HAGHS**.
4.  Follow the setup mask to select your sensors. 

**⚠️ Log File Deprecation:** We are phasing out Log File monitoring to streamline the integration. In the setup mask, please **leave the log file field empty** to skip this check.

---

## Label Configuration (Smart Whitelisting)
To prevent false positives from sleeping tablets or seasonal devices:
1.  Go to **Settings > Devices & Services > Labels**.
2.  Create a label named `haghs_ignore`.
3.  Assign this label to any **Device** or **Entity**. 
    * **Pro Tip:** Assigning the label to a **Device** automatically whitelists **all underlying entities** belonging to that specific device.

---

## Roadmap
* **Custom Thresholds:** Adjust DB limits to your hardware (e.g., for large SSD users).
* **Time-Trigger:** Configure the score to update every 15/30/60 minutes to save resources.
* **Beta Support:** Special logic for users running Home Assistant Beta versions (no version lag penalty).

---

## UI Integration Example

![HAGHS Dashboard example](https://github.com/user-attachments/assets/c3efb257-7350-4612-b9eb-caebd8e93674)


Recommended configuration for a clean frontend display:

```yaml
type: vertical-stack
cards:
  - type: gauge
    entity: sensor.system_ha_global_health_score
    name: HAGHS
    needle: true
    severity:
      green: 90
      yellow: 75
      red: 0
  - type: markdown
    content: >
      **🛡️ Advisor Recommendations:** {{
      state_attr('sensor.system_ha_global_health_score', 'recommendations') }}

      {% set z_list = state_attr('sensor.system_ha_global_health_score',
      'zombie_entities') %} {% if z_list and z_list != 'None' %} **⚠️ Zombie
      Entities:** {{ z_list.split(',') | count }} detected *(Check attributes to
      see full list)* {% endif %}
```
---

## FAQ

**Why is my score so low?**
Check the `recommendations` attribute of your `sensor.system_ha_global_health_score`. It will tell you exactly where the penalties are coming from (e.g., "Delete 45 zombie entities").

**Does this work with Docker?**
Yes! As long as you expose the system metrics via the `systemmonitor` integration and provide the database size via a sensor.

---

## Changelog

### [v2.1.1] - 2026-01-29
* **UI Migration:** Transitioned from YAML variables to a full **Config Flow (Setup Mask)**.
* **Optimization:** `haghs_ignore` label on a Device now automatically covers all its entities.

### [v2.0.2] - 2026-01-26
* **Refinement:** Made Log File monitoring explicitly optional to support HAOS users without CLI access.

### [v2.0.0] - 2026-01-26
* **Major:** Added **Database & Log Hygiene** monitoring.
* **Feature:** Implemented **Deep Label Support**.
* **Logic:** Added **Core Age** penalty (>2 months lag).
* **Logic:** Added **Cumulative Update** counting (capped at 35 pts).

### [v1.3.0] - 2026-01-24
* **NEW:** Implemented Single-Point Configuration using Template Variables.
* **NEW:** Added Heavyweight CPU Tiers.
* **Fixed:** Switched to **Floor Rounding** (Integer) for a more honest health assessment.

---

**AI Disclosure:** While the architectural concept and logic are my own, I utilized AI to assist with code optimization and documentation formatting.
