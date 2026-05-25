"""Testa o serviço koreader.show_message."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN, SERVICE_SHOW_MESSAGE

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_show_message_enqueues(hass: HomeAssistant):
    entry = await _setup(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_SHOW_MESSAGE)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SHOW_MESSAGE,
        {"message": "Hora de dormir", "timeout": 10},
        blocking=True,
    )
    assert entry.runtime_data.commands == [
        {"type": "show_message", "text": "Hora de dormir", "timeout": 10}
    ]
