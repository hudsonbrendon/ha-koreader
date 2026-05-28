"""Testa o switch de wifi."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_wifi_reads_state(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"wifi_connected": True})
    await hass.async_block_till_done()
    assert hass.states.get("switch.koreader_wifi").state == "on"


async def test_turn_off_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.koreader_wifi"},
        blocking=True,
    )
    assert entry.runtime_data.queue.pending == [{"type": "set_wifi", "value": False}]


async def test_frontlight_switch_reads_state(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"frontlight_on": True})
    await hass.async_block_till_done()
    assert hass.states.get("switch.koreader_frontlight").state == "on"


async def test_frontlight_switch_turn_on_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.koreader_frontlight"},
        blocking=True,
    )
    assert entry.runtime_data.queue.pending == [
        {"type": "set_frontlight_power", "value": True}
    ]


async def test_dark_mode_turn_on_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.koreader_dark_mode"}, blocking=True
    )
    assert entry.runtime_data.queue.pending == [
        {"type": "set_dark_mode", "value": True}
    ]
    assert hass.states.get("switch.koreader_dark_mode").state == "on"


async def test_dark_mode_turn_off_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.koreader_dark_mode"}, blocking=True
    )
    assert entry.runtime_data.queue.pending == [
        {"type": "set_dark_mode", "value": False}
    ]
    assert hass.states.get("switch.koreader_dark_mode").state == "off"
