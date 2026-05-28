"""Testa que o webhook popula os sensores."""

from homeassistant.components import webhook
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"

PAYLOAD = {
    "reading": True,
    "device_model": "Kindle Oasis",
    "battery_level": 87,
    "book_title": "Duna",
    "book_author": "Frank Herbert",
    "progress_percent": 31,
    "current_page": 130,
    "total_pages": 412,
    "chapter": "Capítulo 5",
    "reading_time_today_min": 35,
    "pages_read_today": 40,
    "session_time_min": 12,
    "reading_speed_pph": 68,
    "pages_left": 282,
    "pages_left_chapter": 12,
    "time_to_finish_book_min": 250,
    "time_to_finish_chapter_min": 11,
    "book_format": "EPUB",
    "book_language": "pt-BR",
    "book_series": "Crônicas de Duna",
    "total_time_min": 1200,
    "annotations_count": 7,
    "highlights_count": 5,
    "notes_count": 2,
    "koreader_version": "v2024.04",
    "last_seen": "2026-05-25T12:00:00Z",
}


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_sensors_update_from_webhook(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    resp = await client.post(f"/api/webhook/{WEBHOOK_ID}", json=PAYLOAD)
    assert resp.status == 200
    await hass.async_block_till_done()

    assert hass.states.get("sensor.koreader_battery").state == "87"
    assert hass.states.get("sensor.koreader_progress").state == "31"
    assert hass.states.get("sensor.koreader_current_page").state == "130"
    assert hass.states.get("sensor.koreader_chapter").state == "Capítulo 5"
    assert hass.states.get("sensor.koreader_reading_speed").state == "68"
    assert hass.states.get("sensor.koreader_book_title").state == "Duna"


async def test_new_sensors_update_from_webhook(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    resp = await client.post(f"/api/webhook/{WEBHOOK_ID}", json=PAYLOAD)
    assert resp.status == 200
    await hass.async_block_till_done()

    assert hass.states.get("sensor.koreader_pages_left").state == "282"
    assert hass.states.get("sensor.koreader_time_to_finish_book").state == "250"
    assert hass.states.get("sensor.koreader_book_language").state == "pt-BR"
    assert hass.states.get("sensor.koreader_total_reading_time").state == "1200"
    assert hass.states.get("sensor.koreader_annotations").state == "7"
    assert hass.states.get("sensor.koreader_highlights").state == "5"
    assert hass.states.get("sensor.koreader_notes").state == "2"


async def test_device_sw_version_from_koreader_version(
    hass: HomeAssistant, hass_client_no_auth
):
    from homeassistant.helpers import device_registry as dr

    entry = await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json=PAYLOAD)
    await hass.async_block_till_done()

    device = dr.async_get(hass).async_get_device(
        identifiers={(DOMAIN, entry.entry_id)}
    )
    assert device is not None
    assert device.sw_version == "v2024.04"


async def test_battery_has_device_class(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json=PAYLOAD)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.koreader_battery")
    assert state.attributes["device_class"] == "battery"
    assert state.attributes["unit_of_measurement"] == "%"
