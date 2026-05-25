"""Testa os binary sensors."""

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


async def test_binary_sensors(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(
        f"/api/webhook/{WEBHOOK_ID}",
        json={"reading": True, "is_charging": False},
    )
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.koreader_reading").state == "on"
    assert hass.states.get("binary_sensor.koreader_charging").state == "off"
    assert (
        hass.states.get("binary_sensor.koreader_charging").attributes["device_class"]
        == "battery_charging"
    )
