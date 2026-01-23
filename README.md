# 🛡️ HAGHS: Home Assistant Global Health Score
**A Technical Specification for System Stability and Hygiene Standardized Monitoring.**

[![HAGHS Standard](https://img.shields.io/badge/HAGHS-Standard-blue?style=for-the-badge&logo=home-assistant&logoColor=white)](https://github.com/d-n91/home-assistant-global-health-score)
[![Release](https://img.shields.io/badge/Version-1.2.0-green?style=for-the-badge)](https://github.com/d-n91/home-assistant-global-health-score/releases)
[![My HAGHS Score](https://img.shields.io/badge/HAGHS-94%20%2F%20100-brightgreen?style=for-the-badge&logo=home-assistant)](https://github.com/d-n91/home-assistant-global-health-score)
![AI-Powered](https://img.shields.io/badge/Developed%20with-AI-blue?style=for-the-badge&logo=google-gemini&logoColor=white)

## 📄 Abstract
As Home Assistant matures into a mission-critical Smart Home OS, the need for a unified stability metric becomes paramount. **HAGHS** is a logical framework designed to provide an objective **Health Index (0-100)**. It differentiates between transient hardware load and chronic maintenance neglect, providing users with a "North Star" for instance optimization.

---

## 🏗️ The HAGHS Standard (v1.2)

The index is calculated via a weighted average of two core pillars, prioritizing long-term software hygiene over temporary hardware fluctuations.

### The Global Formula

$$Score_{Global} = (Score_{Hardware} \cdot 0.4) + (Score_{Application} \cdot 0.6)$$

---

## 🛠️ Pillar 1: Hardware Performance (40%)

The Hardware Score evaluates the physical constraints of the host machine. It utilizes intelligent thresholding to account for native Linux/Docker overhead.

### Logic & Constraints:
* **CPU Load:** Linear deduction ($0.2$ points per $1\%$ load).
* **Memory Pressure:** Non-linear deduction. Penalties only apply above **70% usage** to respect native Supervisor overhead.
* **Storage Integrity:** Critical deduction when disk usage exceeds **80%**, escalating as the system nears the 95% "database-locking" threshold.

---

## 🧹 Pillar 2: Application Hygiene (60%)

The Application Score measures the "maintenance debt" of the instance.

### The "Fair-Play" Engine:
To remain useful for complex environments, HAGHS implements **Penalty Capping**:
* **Zombie Entities:** Unavailable or Unknown entities are scanned across the registry.
* **Domain Filtering:** Legitimate sleepers (e.g., `device_tracker`, `button`, `scene`, `group`) are excluded to prevent false negatives.
* **Capping:** The total deduction for "Zombies" is capped at **20 points**, ensuring the score remains actionable.
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
3. **Integration:** Paste into your `template.yaml` (without the top-level `template:` key) or directly into `configuration.yaml`.
4. **Entity Alignment:** Update the entity IDs in the **Configuration Block** at the top of the file.
5. **Reload:** Go to **Developer Tools > YAML** and reload **Templates**.

---

## 🏆 Show Your Score
Add this to your GitHub profile or Forum signature:
`[![My HAGHS Score](https://img.shields.io/badge/HAGHS-94%20%2F%20100-brightgreen?style=flat-square&logo=home-assistant)](https://github.com/yourusername/home-assistant-global-health-score)`

---

## 🚀 Reference Implementation
A functional PoC is provided in [`haghs.yaml`](./haghs.yaml).

### UI Integration Example
![HAGHS Dashboard example](https://github.com/user-attachments/assets/5d91ef34-af89-4730-99f0-c67d21eea75a)

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
      ### 🛡️ Advisor Recommendations:
      {{ state_attr('sensor.system_ha_global_health_score', 'recommendations') }}

      {% if state_attr('sensor.system_ha_global_health_score', 'zombie_entities') != 'None' %}
      **Entities to check:**
      {{ state_attr('sensor.system_ha_global_health_score', 'zombie_entities') }}
      {% endif %}

```
---

### 🤖 AI Disclosure
This project was developed in collaboration with **AI**. While the architectural concept and "Fair-Play" logic were designed by me, the AI assisted in code optimization, standardized naming conventions, and documentation formatting.
