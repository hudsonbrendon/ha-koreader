"""Testa o binary_sensor de conectividade e o sensor de último check-in."""

from datetime import timedelta

from freezegun import freeze_time

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_connectivity_off_before_any_checkin(hass: HomeAssistant):
    await _setup(hass)
    state = hass.states.get("binary_sensor.koreader_status")
    assert state is not None
    assert state.state == "off"
    assert state.attributes["device_class"] == "connectivity"


async def test_connectivity_on_after_checkin(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"battery_level": 50})
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.koreader_status").state == "on"


async def test_connectivity_goes_off_after_timeout(
    hass: HomeAssistant, hass_client_no_auth
):
    await _setup(hass)
    client = await hass_client_no_auth()
    start = dt_util.utcnow()
    with freeze_time(start):
        await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"battery_level": 50})
        await hass.async_block_till_done()
        assert hass.states.get("binary_sensor.koreader_status").state == "on"

    later = start + timedelta(minutes=20)
    with freeze_time(later):
        async_fire_time_changed(hass, later)
        await hass.async_block_till_done()
        assert hass.states.get("binary_sensor.koreader_status").state == "off"


async def test_last_checkin_sensor_records_timestamp(
    hass: HomeAssistant, hass_client_no_auth
):
    await _setup(hass)
    state = hass.states.get("sensor.koreader_last_check_in")
    assert state is not None
    assert state.attributes["device_class"] == "timestamp"
    assert state.state in ("unknown", "unavailable")

    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"battery_level": 50})
    await hass.async_block_till_done()
    state = hass.states.get("sensor.koreader_last_check_in")
    assert state.state not in ("unknown", "unavailable")
