# 🛡️ HAGHS: Home Assistant Global Health Score
**A Technical Specification for System Stability and Hygiene Standardized Monitoring.**

[![HAGHS Standard](https://img.shields.io/badge/HAGHS-Standard-blue?style=for-the-badge&logo=home-assistant&logoColor=white)](https://github.com/d-n91/home-assistant-global-health-score)
[![Release](https://img.shields.io/badge/Version-1.3.0-green?style=for-the-badge)](https://github.com/d-n91/home-assistant-global-health-score/releases)
[![My HAGHS Score](https://img.shields.io/badge/HAGHS-98%20%2F%20100-brightgreen?style=for-the-badge&logo=home-assistant)](https://github.com/d-n91/home-assistant-global-health-score)
![AI-Powered](https://img.shields.io/badge/Developed%20with-AI-blue?style=for-the-badge&logo=google-gemini&logoColor=white)

## 📄 Abstract
As Home Assistant matures into a mission-critical Smart Home OS, the need for a unified stability metric becomes paramount. **HAGHS** is a logical framework designed to provide an objective **Health Index (0-100)**. It differentiates between transient hardware load and chronic maintenance neglect, providing users with a "North Star" for instance optimization.

---

## 🏗️ The HAGHS Standard (v1.3)

The index is calculated via a weighted average of two core pillars, prioritizing long-term software hygiene over temporary hardware fluctuations.

### The Global Formula

$$Score_{Global} = \lfloor (Score_{Hardware} \cdot 0.4) + (Score_{Application} \cdot 0.6) \rfloor$$

*Note: As of v1.3, we use **Floor Rounding** (Integer) to ensure a "Perfect 100" is only achieved by truly optimized systems. Even a minor penalty will drop the score to 99.*

---

## 🛠️ Pillar 1: Hardware Performance (40%)

The Hardware Score evaluates the physical constraints of the host machine. v1.3 introduced **Heavyweight CPU Tiers** to penalize background "noise" that impacts system snappiness.



### Logic & Constraints:
* **CPU Load (Tiered):** * 0-10%: **0 pts** (Ideal)
    * 11-15%: **-10 pts**
    * 16-25%: **-25 pts**
    * 26-50%: **-50 pts**
    * \>50%: **-80 pts**
* **Memory Pressure:** Non-linear deduction. Penalties only apply above **70% usage** to respect native Supervisor overhead.
* **Storage Integrity:** Critical deduction when disk usage exceeds **80%**, escalating as the system nears the 95% "database-locking" threshold.

---

## 🧹 Pillar 2: Application Hygiene (60%)

The Application Score measures the "maintenance debt" of the instance.

### The "Fair-Play" Engine:
To remain useful for complex environments, HAGHS implements **Penalty Capping**:
* **Zombie Entities:** Unavailable or Unknown entities are scanned across the registry.
* **Domain Filtering:** Legitimate sleepers (e.g., `button`, `scene`, `group`, `automation`, `device_tracker`) are excluded to prevent false negatives.
* **Integration Health:** Monitors core integration status. Each "unhealthy" integration results in a **5-point deduction**.
* **Capping:** The total deduction for "Zombies" is capped at **20 points**.
* **Safety Net:** A static **30-point deduction** for stale backups and **5 points** for pending core updates.

---

## 📋 Implementation Standards

### Naming Convention
To ensure registry organization, all HAGHS entities follow the professional standard:
`Area: Object - Function` (e.g., `sensor.system_ha_global_health_score`).

### The Advisor Logic
Every HAGHS implementation includes a `recommendations` attribute. This engine parses sub-score failures and provides readable repair steps.

---

## 🚀 Deployment & Usage

1. **Requirements:** Active [System Monitor](https://www.home-assistant.io/integrations/systemmonitor/) integration.
2. **Copy Code:** Download [`haghs.yaml`](./haghs.yaml).
3. **Integration:** Paste into your `template.yaml`.
4. **Single-Point Config:** Update the entity IDs **only once** in the `variables:` block at the top of the file.
5. **Reload:** Go to **Developer Tools > YAML** and reload **Templates**.

---

## 🏆 Show Your Score
Add this to your GitHub profile or Forum signature:
`[![My HAGHS Score](https://img.shields.io/badge/HAGHS-94%20%2F%20100-brightgreen?style=flat-square&logo=home-assistant)](https://github.com/YOURUSERNAME/home-assistant-global-health-score)`

---

## 🚀 Reference Implementation
A functional PoC is provided in [`haghs.yaml`](./haghs.yaml).

### UI Integration Example
<img width="1076" height="733" alt="Screenshot_20260124-004731" src="https://github.com/user-attachments/assets/2224d519-63d1-41c3-aadc-dbaf6eb6fc37" />


```yaml
type: vertical-stack
cards:
  - type: gauge
    entity: sensor.system_ha_global_health_score
    name: HAGHS Index
    needle: true
    severity:
      green: 90
      yellow: 75
      red: 0
  - type: markdown
    content: >
      **Advisor Recommendations:** {{
      state_attr('sensor.system_ha_global_health_score', 'recommendations') }}

      {% if state_attr('sensor.system_ha_global_health_score',
      'zombie_entities') != 'None' %} **Entities to check:** {{
      state_attr('sensor.system_ha_global_health_score', 'zombie_entities') }}
      {% endif %}

```
---

**🤖 AI Disclosure**
This project was developed in collaboration with **AI**. While the architectural concept and logic were designed by me, the AI assisted in code optimization, standardized naming conventions, and documentation formatting.

---

### 🔄 Changelog

#### [v1.3.0] - 2026-01-24
* **NEW:** Implemented **Single-Point Configuration** using Template Variables.
* **NEW:** Added **Heavyweight CPU Tiers** for stricter health assessment.
* **NEW:** Introduced **Integration Health** monitoring.
* **Fixed:** Switched to Integer rounding (Floor) for a more honest 0-100 score.
* **Fixed:** Disk threshold moved to 80% to avoid premature penalties.
