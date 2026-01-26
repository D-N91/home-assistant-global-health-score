  # HAGHS: Home Assistant Global Health Score
  **A Technical Specification for System Stability and Hygiene Standardized Monitoring.**

  [![HAGHS Standard](https://img.shields.io/badge/HAGHS-Standard-blue?style=for-the-badge&logo=home-assistant&logoColor=white)](https://github.com/d-n91/home-assistant-global-health-score)
  [![Release](https://img.shields.io/badge/Version-2.0.2-green?style=for-the-badge)](https://github.com/d-n91/home-assistant-global-health-score/releases)
  [![My HAGHS Score](https://img.shields.io/badge/HAGHS-86%20%2F%20100-brightgreen?style=for-the-badge&logo=home-assistant)](https://github.com/d-n91/home-assistant-global-health-score)
  ![AI-Powered](https://img.shields.io/badge/Developed%20with-AI-blue?style=for-the-badge&logo=google-gemini&logoColor=white)

  ## Abstract
  As Home Assistant matures into a mission-critical Smart Home OS, the need for a unified stability metric becomes paramount. **HAGHS** is a logical framework designed to provide an objective **Health Index (0-100)**. It differentiates between transient hardware load and chronic maintenance neglect, providing users with a "North Star" for instance optimization.

  ---

  ## The HAGHS Standard (v2.0.2)

  The index is calculated via a weighted average of two core pillars, prioritizing long-term software hygiene over temporary hardware fluctuations.

  ### The Global Formula

  $$Score_{Global} = \lfloor (Score_{Hardware} \cdot 0.4) + (Score_{Application} \cdot 0.6) \rfloor$$

  *Note: We use **Floor Rounding** (Integer) to ensure a "Perfect 100" is only achieved by truly optimized systems. Even a minor penalty will drop the score to 99.*

  ---

  ## Pillar 1: Hardware Performance (40%)

  The Hardware Score evaluates the physical constraints of the host machine. It uses **Heavyweight CPU Tiers** to penalize background noise that impacts system responsiveness.

  ### Logic & Constraints
  * **CPU Load (Tiered):**
    * 0-10%: **0 pts** (Ideal)
    * 11-15%: **-10 pts**
    * 16-25%: **-25 pts**
    * 26-50%: **-50 pts**
    * 50% and more: **-80 pts**
  * **Memory Pressure:** Non-linear deduction. Penalties only apply above **70% usage** to respect native Supervisor overhead.
  * **Storage Integrity:** Critical deduction when disk usage exceeds **80%**, escalating as the system nears the 95% "database-locking" threshold.

  ---

  ## Pillar 2: Application Hygiene (60%)

  The Application Score measures the "maintenance debt" of the instance. v2.0 introduces strict monitoring for database size and log flooding.

  ### The "Fair-Play" Engine
  To remain useful for complex environments, HAGHS implements **Penalty Capping** and **Smart Filtering**:

  * **Zombie Entities:** Checks for `unavailable` or `unknown` states.
    * *Filter:* Entities or Devices marked with the `haghs_ignore` label are automatically whitelisted.
    * *Cap:* Max deduction of **20 points**.
  * **Database Hygiene:** Monitors `home-assistant_v2.db` size.
    * *Warning:* > 1.0 GB (**-10 pts**)
    * *Critical:* > 2.5 GB (**-30 pts**)
  * **Log Hygiene:** Monitors `home-assistant.log` size (spam/error detection).
    * *Warning:* > 20 MB (**-10 pts**)
    * *Critical:* > 100 MB (**-25 pts**)
  * **Updates & Core Age:**
    * *Standard:* **-5 pts** per pending update.
    * *Core Age:* Additional **-20 pts** if Home Assistant Core is > 2 months behind.
    * *Max Penalty:* Capped at **-35 pts**.
  * **Safety Net:** A static **30-point deduction** for stale backups.

  ---

  ## Implementation Standards

  ### Naming Convention
  To ensure registry organization, all HAGHS entities follow the professional standard:
  `Area: Object - Function` (e.g., `sensor.system_ha_global_health_score`).

  ### The Advisor Logic
  Every HAGHS implementation includes a `recommendations` attribute. This engine parses sub-score failures and provides readable repair steps directly in the dashboard.

  ---

  ## Deployment & Usage

  ### 1. Prerequisites

  **A. System Monitor:**
  Ensure the **System Monitor** integration is installed via **Settings > Devices & Services**. This is required to provide the CPU, RAM, and Disk sensors for the hardware pillar.
  
  **B. Database Access (Essential):**
  To monitor your database size (the most critical performance factor), add this to your `configuration.yaml` and restart:
  ```yaml
  homeassistant:
    allowlist_external_dirs:
      - "/config"
  ```
  After restarting, add the **File Size** integration via Settings and track:
  * `/config/home-assistant_v2.db`

  **C. Log File Access (Optional / Advanced):**
  *Standard users can skip this step.*
  By default, Home Assistant OS does not create a physical log file to protect SD cards. If you are an advanced user and want to monitor log spam via HAGHS, you must:
  1. Enable file logging via the Terminal CLI (`ha core options --log-file=true` followed by `ha core restart`).
  2. **Crucial:** Once restarted, go to the **File Size** integration settings and add the path `/config/home-assistant.log` to be tracked.
  
  If you skip this, HAGHS will simply ignore the log-size penalty (graceful degradation).

  ### 2. Installation
  1.  Download [`haghs.yaml`](./haghs.yaml).
  2.  Paste it into your `template.yaml` (or configuration).
  3.  **Single-Point Config:** Update the entity IDs in the `variables:` block at the top of the file to match your system.

  ### 3. Label Configuration
  To prevent false positives (e.g., sleeping tablets or battery devices):
  1.  Go to **Settings > Devices & Services > Labels**.
  2.  Create a label named `haghs_ignore`.
  3.  Assign this label to any Device or Entity you want HAGHS to ignore.

  ---

  ## UI Integration Example

![HAGHS Dashboard example](https://github.com/user-attachments/assets/f1457b91-65a8-4822-8129-a1be86f793bf)


  Recommended configuration for a clean frontend display.

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
      **🛡️ Advisor Recommendations:** {{
      state_attr('sensor.system_ha_global_health_score', 'recommendations') }}

      {% set z_list = state_attr('sensor.system_ha_global_health_score',
      'zombie_entities') %} {% if z_list and z_list != 'None' %} **⚠️ Zombie
      Entities:** {{ z_list.split(',') | count }} detected *(Check attributes to
      see full list)* {% endif %}

  ```

  ---

  ## Changelog

### [v2.0.2] - 2026-01-26
  * **Refinement:** Made Log File monitoring explicitly optional. The system now gracefully handles missing log sensors for HAOS users who prefer not to use the CLI.

  ### [v2.0.0] - 2026-01-26
  * **Major:** Added **Database Hygiene** monitoring (File Size).
  * **Major:** Added **Log File Hygiene** monitoring (File Size).
  * **Feature:** Implemented **Deep Label Support**. Defining `haghs_ignore` on a Device now automatically whitelists all underlying entities.
  * **Logic:** Added **Core Age** penalty. Severe score drop if Core version lags by >2 months.
  * **Logic:** Added **Cumulative Update** counting (capped at 35 pts).
  * **Refinement:** Removed hardcoded regex filters in favor of the label system.

  ### [v1.3.0] - 2026-01-24
  * **NEW:** Implemented Single-Point Configuration using Template Variables.
  * **NEW:** Added Heavyweight CPU Tiers for stricter health assessment.
  * **Fixed:** Switched to Integer rounding (Floor) for a more honest score.
  * **Fixed:** Disk threshold moved to 80% to avoid premature penalties.
    
  ---

  **AI Disclosure**
  This project was developed in collaboration with **AI**. While the architectural concept and logic were designed by me, the AI assisted in code optimization, standardized naming conventions, and documentation formatting.
