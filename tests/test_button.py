"""Testa o button de forçar sync."""

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


async def test_press_enqueues_sync(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.koreader_force_sync"},
        blocking=True,
    )
    assert entry.runtime_data.queue.pending == [{"type": "sync_now"}]


async def test_next_page_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.koreader_next_page"},
        blocking=True,
    )
    assert entry.runtime_data.queue.pending == [{"type": "page_turn", "value": 1}]


async def test_prev_page_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.koreader_previous_page"},
        blocking=True,
    )
    assert entry.runtime_data.queue.pending == [{"type": "page_turn", "value": -1}]


async def test_refresh_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.koreader_refresh_screen"},
        blocking=True,
    )
    assert entry.runtime_data.queue.pending == [{"type": "refresh"}]


async def test_next_chapter_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.koreader_next_chapter"}, blocking=True
    )
    assert entry.runtime_data.queue.pending == [{"type": "goto_chapter", "value": 1}]


async def test_prev_chapter_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.koreader_previous_chapter"},
        blocking=True,
    )
    assert entry.runtime_data.queue.pending == [{"type": "goto_chapter", "value": -1}]


async def test_toggle_bookmark_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.koreader_toggle_bookmark"},
        blocking=True,
    )
    assert entry.runtime_data.queue.pending == [{"type": "toggle_bookmark"}]


async def test_suspend_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.koreader_suspend"}, blocking=True
    )
    assert entry.runtime_data.queue.pending == [{"type": "suspend"}]


async def test_restart_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.koreader_restart"}, blocking=True
    )
    assert entry.runtime_data.queue.pending == [{"type": "restart"}]
