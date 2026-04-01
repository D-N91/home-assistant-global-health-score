# HAGHS Development Guidelines (HA Core Standards)

## 1. Code Quality & Structure
- **Strict Typing:** All Python code must be fully annotated with type hints. The code must pass strict `mypy` checks.
- **Language & Naming:** Code, variables, class names, and comments must be written exclusively in English. Follow PEP 8 standards.
- **Linting:** The code must comply with official Home Assistant standards (using `ruff` for clean linting and formatting).

## 2. Home Assistant Core Rules
- **Async-First (Non-Blocking):** Home Assistant is built on an asynchronous architecture. I/O operations (network, file access) must never block the main event loop. Always use `async def`, `await`, and asynchronous libraries (e.g. `aiohttp` instead of `requests`, `aiofiles`).
- **Setup & Configuration:** YAML configurations for integrations are deprecated. All configuration and options must be handled exclusively through a UI-based `ConfigFlow` and `OptionsFlow`.
- **Data Fetching:** Always use the `DataUpdateCoordinator` for regular updates. No isolated `time.sleep()` or custom loops.
- **Localization (I18n):** Never hardcode user-facing text or error messages directly in Python code. Consistently use `strings.json` and the corresponding translation files (e.g. `en.json`).

## 3. Automation Standards & Logic Efficiency
- **Safety Net:** Always include timeouts and `continue_on_error` to ensure the core logic is never stalled by our scripts or automations.
- **Resource Efficiency:** Use `trigger_id` to consolidate multiple automations efficiently where appropriate. Always evaluate the ideal execution mode (single, restart, parallel).
- **Metrics:** Always use metric units by default for calculations and outputs.
