"""Testa o number do frontlight: lê valor e enfileira comando."""

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


async def test_frontlight_reads_value(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"frontlight": 15})
    await hass.async_block_till_done()
    assert hass.states.get("number.koreader_frontlight").state == "15.0"


async def test_set_frontlight_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.koreader_frontlight", "value": 25},
        blocking=True,
    )
    assert entry.runtime_data.commands == [{"type": "set_frontlight", "value": 25}]
