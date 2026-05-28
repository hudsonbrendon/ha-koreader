<p align="center">
  <img src="https://raw.githubusercontent.com/hudsonbrendon/ha-koreader/main/logo.png" alt="KOReader" width="320">
</p>

# KOReader — Home Assistant Integration

Native Home Assistant integration for **KOReader** running on a Kindle (or any KOReader
device). It ingests reading and device **telemetry** and lets you **control the device**
— frontlight, warmth, wifi, page turns, on-screen messages and more — straight from
Home Assistant.

Companion KOReader plugin: **[hatelemetry.koplugin](https://github.com/hudsonbrendon/hatelemetry.koplugin)**
— sends the telemetry snapshot and applies the commands on the device.

## How it works

On each check-in (page turn, wake-up, or a periodic loop) the plugin sends a snapshot
to Home Assistant. There are two modes:

- **Webhook (native, recommended)** — this integration receives the snapshot, exposes
  every entity below, and sends control commands back to the device in the webhook
  response. Full telemetry **and** control.
- **REST (legacy)** — the plugin writes sensors directly to Home Assistant's
  `/api/states` using a long-lived token. Telemetry only; no control from Home Assistant.

> **e-ink note:** commands only reach the device on its next check-in with WiFi on —
> they are not instant while the screen is off.

## Installation (HACS)

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/hudsonbrendon/ha-koreader` as type **Integration**
3. Install **KOReader** and restart Home Assistant
4. Settings → Devices & Services → **Add integration** → **KOReader**
5. Confirm — Home Assistant shows the **webhook URL**. Copy the id at the end of it.

## Plugin setup

Install **[hatelemetry.koplugin](https://github.com/hudsonbrendon/hatelemetry.koplugin)**
on the device (copy the folder into `koreader/plugins/`), then edit its `ha_config.lua`:

- **Webhook mode:** set `webhook_id` to the copied id, set `host` / `port` / `https`, and
  leave `token = ""`.
- **REST mode:** leave `webhook_id` empty and set `token` to a Home Assistant long-lived
  access token.

Restart KOReader to load the plugin. Use **Tools → HA Telemetry → Test connection** to verify.

## Sensors

| Entity | Description |
|---|---|
| `sensor.koreader_battery` | Battery level (%) |
| `sensor.koreader_book_title` | Current book title |
| `sensor.koreader_book_author` | Current book author |
| `sensor.koreader_book_series` | Book series / collection |
| `sensor.koreader_book_format` | File format (EPUB, PDF, …) |
| `sensor.koreader_book_language` | Book language |
| `sensor.koreader_chapter` | Current chapter |
| `sensor.koreader_progress` | Reading progress (%) |
| `sensor.koreader_current_page` | Current page |
| `sensor.koreader_total_pages` | Total pages |
| `sensor.koreader_pages_left` | Pages left in the book |
| `sensor.koreader_pages_left_in_chapter` | Pages left in the current chapter |
| `sensor.koreader_time_to_finish_book` | Estimated time to finish the book (min) |
| `sensor.koreader_time_to_finish_chapter` | Estimated time to finish the chapter (min) |
| `sensor.koreader_reading_speed` | Reading speed (pages/h) |
| `sensor.koreader_reading_time_today` | Reading time today (min) |
| `sensor.koreader_pages_read_today` | Pages read today |
| `sensor.koreader_session_time` | Current session time (min) |
| `sensor.koreader_total_reading_time` | Lifetime reading time for the book (min) |
| `sensor.koreader_annotations` | Number of highlights / notes (combined) |
| `sensor.koreader_highlights` | Highlights only |
| `sensor.koreader_notes` | Notes only |
| `sensor.koreader_last_check_in` | Timestamp of the last telemetry check-in (HA clock) |
| `sensor.koreader_estimated_finish_date` | Projected finish date/time at the current pace |

## Binary sensors

| Entity | Description |
|---|---|
| `binary_sensor.koreader_reading` | Reading / book open |
| `binary_sensor.koreader_charging` | Device charging |
| `binary_sensor.koreader_status` | Connectivity — `on` while a check-in arrived within the last 15 min |

## Controls

| Entity | Description |
|---|---|
| `number.koreader_frontlight` | Frontlight brightness (0–100%) |
| `number.koreader_warmth` | Frontlight warmth / color temperature |
| `switch.koreader_frontlight` | Frontlight on / off |
| `switch.koreader_wifi` | Wi-Fi on / off |
| `switch.koreader_dark_mode` | Night mode on / off (assumed state) |
| `button.koreader_next_page` | Turn to the next page |
| `button.koreader_previous_page` | Turn to the previous page |
| `button.koreader_next_chapter` | Jump to the next chapter |
| `button.koreader_previous_chapter` | Jump to the previous chapter |
| `button.koreader_toggle_bookmark` | Bookmark the current page |
| `button.koreader_refresh_screen` | Refresh the e-ink screen |
| `button.koreader_suspend` | Put the device to sleep |
| `button.koreader_restart` | Restart KOReader |
| `button.koreader_force_sync` | Force a sync / check-in |
| `notify.koreader_notify` | Notify target — push text to the device screen via `notify.send_message` |

## Services

| Service | Description | Fields |
|---|---|---|
| `koreader.show_message` | Queue a message to show on the device screen | `message` (required), `timeout` (optional, 1–120 s) |
| `koreader.go_to_page` | Queue a jump to a specific page | `page` (required, ≥ 1) |
| `koreader.go_to_percentage` | Queue a jump to a percentage of the book (needs known total pages) | `percent` (required, 0–100) |

## Events & device triggers

On telemetry transitions the integration fires a `koreader_event` bus event (also
surfaced as **device triggers** in the automation UI), carrying `type`, `device_id`
and `entry_id`:

| Type | Fires when |
|---|---|
| `session_started` | The device starts reading |
| `session_ended` | The device stops reading |
| `book_finished` | Progress reaches 100% |
| `book_changed` | The open book title changes |
| `highlight_added` | The annotation count increases |

## Diagnostics

Download diagnostics from the device page (⋮ → **Download diagnostics**) to get the
last snapshot, last check-in time, and any pending commands.

## Architecture

The KOReader protocol logic — telemetry snapshot model, command builders, and the
coalescing command queue — lives in a standalone, Home-Assistant-agnostic Python
package: **[pykoreader](https://github.com/hudsonbrendon/pykoreader)** ([PyPI](https://pypi.org/project/pykoreader/)).
This integration depends on it (declared in `manifest.json` `requirements`, installed
automatically by Home Assistant) and only contains the Home Assistant glue: entities,
config flow, the webhook endpoint, services, and the dashboard. Parsing a webhook body
into a typed `Snapshot` and building/queuing device commands are all handled by
`pykoreader`.

## Dashboard

A ready-to-use Lovelace dashboard is included at
[`docs/home-assistant/dashboard.yaml`](docs/home-assistant/dashboard.yaml).
