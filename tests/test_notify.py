"""Testa a entidade notify que envia mensagens para a tela do KOReader."""

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


async def test_notify_entity_exists(hass: HomeAssistant):
    await _setup(hass)
    assert hass.states.get("notify.koreader_notify") is not None


async def test_notify_enqueues_show_message(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "notify",
        "send_message",
        {"entity_id": "notify.koreader_notify", "message": "Hora de dormir"},
        blocking=True,
    )
    assert entry.runtime_data.queue.pending == [
        {"type": "show_message", "text": "Hora de dormir"}
    ]
