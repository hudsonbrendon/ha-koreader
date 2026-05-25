<p align="center">
  <img src="icon.png" alt="KOReader" width="120"><br>
  <img src="logo.png" alt="KOReader" width="320">
</p>

# KOReader — Home Assistant Integration

Native integration that receives KOReader (Kindle) telemetry via **webhook** and lets
you **control the Kindle** (frontlight, on-screen message, wifi, sync) from Home Assistant.

Translations: 🇬🇧 English (`en`) · 🇧🇷 Português (`pt` / `pt-BR`) · 🇪🇸 Español (`es`).

## Installation (HACS)

1. HACS → Integrations → menu (⋮) → **Custom repositories**
2. Add `https://github.com/hudsonbrendon/ha-koreader` as type **Integration**
3. Install **KOReader** and restart Home Assistant
4. Settings → Devices & Services → **Add integration** → **KOReader**
5. Confirm — Home Assistant shows the **webhook URL**. Copy the id at the end of it.

## Configure the KOReader plugin

In the `ha_config.lua` of the `hatelemetry.koplugin` plugin, set `webhook_id` to the
copied id, adjust `host`/`port`/`https`, and leave `token = ""`. Reinstall the plugin
on the Kindle and restart KOReader.

## Entities

A **KOReader** device with: battery, reading status, charging, title/author,
progress %, current/total page, chapter, reading time today, pages today, session
time, reading speed, frontlight (control), wifi (control), sync button, and the
`koreader.show_message` service.

## Limitation (e-ink)

Commands from Home Assistant only reach the device on KOReader's next check-in (page
turn, wake-up, or periodic loop) with WiFi on. It is not instant while the screen is off.
