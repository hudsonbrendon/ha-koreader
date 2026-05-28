"""Testa o sensor de data estimada de término."""

from datetime import timedelta

from freezegun import freeze_time

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

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


async def test_finish_date_is_now_plus_eta(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    start = dt_util.utcnow().replace(microsecond=0)
    with freeze_time(start):
        await client.post(
            f"/api/webhook/{WEBHOOK_ID}", json={"time_to_finish_book_min": 120}
        )
        await hass.async_block_till_done()
        state = hass.states.get("sensor.koreader_estimated_finish_date")
        assert state.attributes["device_class"] == "timestamp"
        expected = (start + timedelta(minutes=120)).isoformat()
        assert dt_util.parse_datetime(state.state) == dt_util.parse_datetime(expected)


async def test_finish_date_unknown_without_eta(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"battery_level": 50})
    await hass.async_block_till_done()
    state = hass.states.get("sensor.koreader_estimated_finish_date")
    assert state.state == "unknown"
