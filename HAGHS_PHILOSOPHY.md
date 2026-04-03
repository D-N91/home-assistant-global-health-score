# HAGHS Vision & Alignment Rules
- **Core Focus:** HAGHS serves exclusively system health. Features that are purely decorative are treated with low priority or rejected.
- **Local Only:** All data collection must remain local. HAGHS must never depend on external APIs or cloud services. Every new feature must be verified to not introduce outbound network traffic.
- **Pragmatism:** The simplest effective solution always wins, followed by a deeper technical explanation. Accuracy is more important than simplicity.
- **Transparency:** All scoring logic must be fully visible in the codebase. No hidden penalties, no obfuscated thresholds.
- **Backward Compatibility:** Score changes between versions must be documented and justified. Users should understand why their score changed after an update. Renaming or removing sensor attributes is a breaking change.
- **Vision of HAGHS:** Short-term: Establish HAGHS as the community standard for instance health monitoring. Long-term: Propose adoption into HA Core. With user consent, HAGHS metrics and data should be analyzed so Home Assistant knows exactly how the software is being used and how healthy the instances are.
