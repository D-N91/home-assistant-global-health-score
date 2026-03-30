# HAGHS Development Guidelines (HA Core Standards)

## 1. Code-Qualität & Struktur
- **Strict Typing:** Sämtlicher Python-Code muss vollständig mit Type Hints versehen sein. Der Code muss strikte `mypy`-Checks bestehen.
- **Sprache & Naming:** Code, Variablen, Klassennamen und Kommentare sind ausnahmslos auf Englisch zu verfassen. Halte dich an die PEP 8 Standards.
- **Linting:** Der Code muss den offiziellen Home Assistant Standards entsprechen (Nutzung von `ruff` für sauberes Linting und Formatting).

## 2. Home Assistant Core Rules
- **Async-First (Non-Blocking):** Home Assistant basiert auf einer asynchronen Architektur. I/O-Operationen (Netzwerk, Dateizugriffe) dürfen den Main Event Loop niemals blockieren. Nutze zwingend `async def`, `await` und asynchrone Bibliotheken (z. B. `aiohttp` statt `requests`, `aiofiles`).
- **Setup & Konfiguration:** YAML-Konfigurationen für Integrationen sind deprecated. Sämtliche Konfigurationen und Optionen müssen zwingend über einen UI-basierten `ConfigFlow` und `OptionsFlow` abgewickelt werden.
- **Datenbeschaffung:** Nutze für regelmäßige Updates immer den `DataUpdateCoordinator`. Keine isolierten `time.sleep()` oder eigenen Schleifen.
- **Lokalisierung (I18n):** Hardcode niemals benutzerlesbare Texte oder Fehlermeldungen direkt im Python-Code. Nutze konsequent `strings.json` und die entsprechenden Übersetzungsdateien (z. B. `en.json`).

## 3. Automations-Standards & Logik-Effizienz
- **Sicherheitsnetz:** Baue zwingend Timeouts und `continue_on_error` ein, damit die Core-Logik niemals durch unsere Skripte oder Automationen zum Stehen kommt.
- **Ressourcen-Schonung:** Nutze `trigger_id`, um mehrere Automationen effizient zusammenzufassen, wenn es sinnvoll ist. Prüfe immer den idealen Ausführungsmodus (single, restart, parallel).
- **Metriken:** Verwende standardmäßig immer metrische Einheiten für Berechnungen und Ausgaben.