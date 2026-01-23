# 🛡️ HAGHS: Home Assistant Global Health Score
**A Technical Specification for System Stability and Hygiene Standardized Monitoring.**

[![HAGHS Standard](https://img.shields.io/badge/HAGHS-Standard-blue?style=for-the-badge&logo=home-assistant&logoColor=white)](https://github.com/d-n91/home-assistant-global-health-score)
[![Release](https://img.shields.io/badge/Version-1.1.0-green?style=for-the-badge)](https://github.com/d-n91/home-assistant-global-health-score/releases)

## 📄 Abstract
As Home Assistant matures into a mission-critical Smart Home OS, the need for a unified stability metric becomes paramount. **HAGHS** is a logical framework designed to provide an objective **Health Index (0-100)**. It differentiates between transient hardware load and chronic maintenance neglect, providing users with a "North Star" for instance optimization.

---

## 🏗️ The HAGHS Standard (v1.1)

The index is calculated via a weighted average of two core pillars, prioritizing long-term software hygiene over temporary hardware fluctuations.

### The Global Formula

$$Score_{Global} = (Score_{Hardware} \cdot 0.4) + (Score_{Application} \cdot 0.6)$$

---

## 🛠️ Pillar 1: Hardware Performance (40%)

The Hardware Score evaluates the physical constraints of the host machine. It utilizes intelligent thresholding to account for native Linux/Docker overhead.

### Logic & Constraints:
* **CPU Load:** Linear deduction ($0.2$ points per $1\%$ load).
* **Memory Pressure:** Non-linear deduction. Penalties only apply above **70% usage** to respect legitimate reservations from Java-based add-ons and Supervisor overhead.
* **Storage Integrity:** Critical deduction when disk usage exceeds **80%**, escalating as the system nears the 95% "database-locking" threshold.

---

## 🧹 Pillar 2: Application Hygiene (60%)

The Application Score measures the "maintenance debt" of the instance. This is the primary indicator of long-term stability and conflict prevention.

### The "Fair-Play" Engine:
To remain useful for complex environments, HAGHS implements **Penalty Capping**:
* **Zombie Entities:** Unavailable or Unknown entities are scanned across the registry.
* **Domain Filtering:** Legitimate sleepers (e.g., `device_tracker`, `button`, `scene`) are excluded to prevent false negatives.
* **Capping:** The total deduction for "Zombies" is capped at **20 points**, ensuring the score remains actionable even if users have intentional offline devices.
* **Safety Net:** A static **30-point deduction** is applied if the system detects a stale backup state or critical security updates are ignored.

---

## 📋 Implementation Standards

### Naming Convention
To ensure registry organization and prevent automation conflicts, all HAGHS entities follow the professional standard:
`Area: Object - Function` (e.g., `sensor.system_ha_global_health_score`).

### The Advisor Logic
Every HAGHS implementation includes a `recommendations` attribute. This engine parses sub-score failures and provides human-readable, prioritized repair steps.

---

## 🚀 Reference Implementation
A functional Proof of Concept (PoC) using the Home Assistant Template Engine is provided in [`haghs.yaml`](./haghs.yaml).

### UI Integration Example
![HAGHS Dashboard example](https://github.com/user-attachments/assets/6eefb5fa-b646-4777-a2a1-8a3706ce453d)

```yaml
type: vertical-stack
cards:
  - type: gauge
    entity: sensor.system_ha_global_health_score
    name: HAGHS Index
    min: 0
    max: 100
    needle: true
    severity:
      green: 90
      yellow: 75
      red: 0
  - type: markdown
    content: >
      **Advisor Recommendations:**

      {{ state_attr('sensor.system_ha_global_health_score', 'recommendations')
      }}
