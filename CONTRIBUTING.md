# Contributing to HAGHS

Thanks for considering a contribution. HAGHS (Home Assistant Global Health
Score) aims to become the community standard for Home Assistant instance
health monitoring, with a long-term path into HA Core. To keep that path
open, contributions must follow the project's engineering and philosophical
standards.

## Before You Open a Pull Request

**Mandatory reading:**

1. [`HAGHS_PHILOSOPHY.md`](./HAGHS_PHILOSOPHY.md) — vision, scope, hard rules
   on local-only data, transparency and backward compatibility.
2. [`DEVELOPMENT_GUIDELINES.md`](./DEVELOPMENT_GUIDELINES.md) — Home Assistant
   Core coding standards we align with.

If your PR contradicts either document, it will be asked to change or be
closed.

## Branching

- Target branch for all PRs: **`dev`**. Never open PRs against `main`.
- `main` is release-only and is updated by the maintainer through a
  controlled `dev` → `main` merge after CI and manual validation.
- Create your feature branch off the latest `dev`.

## Language

- All code, variables, class names, docstrings, comments, commit messages,
  PR titles, PR descriptions and review discussion: **English only**.
- User-facing text belongs in `strings.json` + `translations/*.json`, never
  hardcoded in Python.

## Changelog

- Every change that lands on `dev` must include a matching entry in
  `v2.3_CHANGELOG.md` (or the current active changelog file).
- The entry should describe the *why*, list files touched, and flag any
  behavior change users might notice.
- Silent behavior changes (constant removal, default changes, etc.) must be
  explicitly called out.

## Scope

- One topic per PR. Split refactors, features and fixes.
- Purely decorative features (UI polish unrelated to health signals) are
  low priority or declined — see `HAGHS_PHILOSOPHY.md` §Core Focus.
- Don't refactor neighboring code unless it's necessary for the change.

## Hard Rules

### Local-only

- No outbound network calls. No external APIs. No cloud services.
- Every new dependency must be audited for embedded telemetry.

### Backward compatibility

- Score formulas that change between versions need justification in the
  changelog so users understand why their score moved.
- Renaming or removing sensor attributes is a breaking change and requires
  either a migration (`async_migrate_entry`) or a major version bump with
  release notes.
- Removing constants or defaults that users relied on is also a breaking
  change — document it.

### Home Assistant Core rules

- **Async-first.** Any I/O must go through `async def` / `await` or
  `hass.async_add_executor_job(...)`. Blocking the event loop will be
  rejected.
- **Config Flow / Options Flow only.** YAML configuration is deprecated and
  will not be accepted.
- **DataUpdateCoordinator.** All periodic work goes through the coordinator.
  No standalone `time.sleep` loops.
- **Safety net.** New scoring sub-calculations must use the `_safe_calc`
  pattern with a timeout. A failing pillar must never crash the sensor or
  raise out of the coordinator.

### Localization

- All user-facing strings live in `strings.json`.
- `translations/en.json` must mirror `strings.json` 1:1.
- Translation keys used at runtime must match exactly — mismatches are a
  blocker, not a nit.

### Code quality

- Type hints on every public function and method (PEP 484 / strict mode).
- Formatting and linting: `ruff` clean.
- PEP 8 naming. Module-private names start with a single underscore.

## Tests

Once the test infrastructure lands (see the test-bootstrap tracking issue),
the following are required:

- New scoring logic: unit tests with known input/output pairs.
- Migration logic: tests for every branch (value present / absent, label
  exists / doesn't exist, race conditions).

Until then, describe your manual validation steps in the PR description
under "Test plan".

## Review Process

- Maintainer is `@D-N91`.
- Responses in English only, including on community forums.
- The trigger phrase **"Are you sure?"** from the maintainer means: stop,
  re-evaluate all sources and reasoning, then respond.
- Expect at least one review round before merge. Don't force-push during an
  active review — append commits; the maintainer may squash on merge.

## Reporting Issues Instead

If you're not sure whether a change is wanted, open an issue first. It's
cheaper than a rejected PR.
