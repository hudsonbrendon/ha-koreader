"""Testa os gatilhos de dispositivo (device triggers) do KOReader."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from custom_components.koreader.const import DOMAIN, EVENT_TYPES

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _device_id(hass, entry) -> str:
    device = dr.async_get(hass).async_get_device(
        identifiers={(DOMAIN, entry.entry_id)}
    )
    assert device is not None
    return device.id


async def test_get_triggers_lists_all_event_types(hass: HomeAssistant):
    from custom_components.koreader import device_trigger

    entry = await _setup(hass)
    triggers = await device_trigger.async_get_triggers(hass, _device_id(hass, entry))
    types = {t["type"] for t in triggers}
    assert types == set(EVENT_TYPES)


async def test_device_trigger_fires_automation(
    hass: HomeAssistant, hass_client_no_auth
):
    entry = await _setup(hass)
    device_id = _device_id(hass, entry)

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {
                    "platform": "device",
                    "domain": DOMAIN,
                    "device_id": device_id,
                    "type": "book_finished",
                },
                "action": {"event": "koreader_test_fired"},
            }
        },
    )
    await hass.async_block_till_done()

    fired = async_capture_events(hass, "koreader_test_fired")
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"progress_percent": 80})
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"progress_percent": 100})
    await hass.async_block_till_done()

    assert len(fired) == 1
