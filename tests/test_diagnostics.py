"""Testa o payload de diagnostics da entry."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN
from custom_components.koreader.diagnostics import (
    async_get_config_entry_diagnostics,
)

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_diagnostics_includes_snapshot_and_queue(
    hass: HomeAssistant, hass_client_no_auth
):
    entry = await _setup(hass)
    entry.runtime_data.queue.add({"type": "refresh"})
    client = await hass_client_no_auth()
    await client.post(
        f"/api/webhook/{WEBHOOK_ID}", json={"battery_level": 50, "book_title": "Duna"}
    )
    await hass.async_block_till_done()
    # Re-enfileira após o drain do webhook para checar a serialização da fila.
    entry.runtime_data.queue.add({"type": "refresh"})

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["snapshot"]["battery_level"] == 50
    assert diag["snapshot"]["book_title"] == "Duna"
    assert diag["last_update"] is not None
    assert diag["pending_commands"] == [{"type": "refresh"}]


async def test_diagnostics_without_snapshot(hass: HomeAssistant):
    entry = await _setup(hass)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["snapshot"] is None
    assert diag["last_update"] is None
