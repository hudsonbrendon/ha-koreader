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
    assert entry.runtime_data.commands == [{"type": "sync_now"}]
