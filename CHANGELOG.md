# Changelog

## 0.6.1 - Unreleased

Modernised for Home Assistant 2026.10 / Python 3.14. No behaviour change.

- Replace deprecated `device_registry.async_get_device(identifiers=...)` with
  `async_get_device_by_identifier` (removal scheduled for HA 2027.8).
- Register the `show_message`, `go_to_page` and `go_to_percentage` actions
  from `async_setup` via `services.py` instead of per config entry.
- `PARALLEL_UPDATES` and `AddConfigEntryEntitiesCallback` on every platform;
  typed `KOReaderConfigEntry` throughout.
- Diagnostics now include the config entry with the webhook id redacted.
- `manifest.json`: `loggers`; `strings.json` is now English and identical to
  `translations/en.json`; `quality_scale.yaml` added.
- Tooling: `pyproject.toml` (ruff + pytest), test deps pinned to
  `pytest-homeassistant-custom-component==0.13.375`, GitHub workflows for
  tests (Python 3.14), hassfest, HACS validation and release; HACS floor
  raised to 2026.10.0.
