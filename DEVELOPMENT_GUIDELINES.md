# HAGHS Development Guidelines (HA Core Standards)

## 1. Code Quality & Structure
- **Strict Typing:** All Python code must be annotated with type hints. Type hints are required for all public methods and function signatures.
- **Language & Naming:** Code, variables, class names, and comments must be written exclusively in English. Follow PEP 8 standards.
- **Linting:** The code must comply with official Home Assistant standards (using `ruff` for clean linting and formatting).

## 2. Home Assistant Core Rules
- **Async-First (Non-Blocking):** Home Assistant is built on an asynchronous architecture. I/O operations (network, file access) must never block the main event loop. Always use `async def`, `await`, and asynchronous libraries (e.g. `aiohttp` instead of `requests`, `aiofiles`).
- **Setup & Configuration:** YAML configurations for integrations are deprecated. All configuration and options must be handled exclusively through a UI-based `ConfigFlow` and `OptionsFlow`.
- **Data Fetching:** Always use the `DataUpdateCoordinator` for regular updates. No isolated `time.sleep()` or custom loops.
- **Localization (I18n):** Never hardcode user-facing text or error messages directly in Python code. Consistently use `strings.json` and the corresponding translation files (e.g. `en.json`).

## 3. Safety & Stability
- **Safety Net:** All sub-calculations must use the safety-net pattern (`_safe_calc` with timeout). A failing pillar must never crash the sensor. The coordinator itself must never raise.
- **Error Handling:** Use `continue_on_error` and timeouts to ensure core logic is never stalled. Log warnings for degraded states instead of raising exceptions.
- **Testing:** All new scoring logic should include unit tests with known input/output pairs. This is a prerequisite for HA Core adoption.
