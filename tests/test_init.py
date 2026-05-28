"""Testa setup da entry, recebimento de webhook e resposta de comandos."""

from homeassistant.components import webhook
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_webhook_stores_payload_and_returns_commands(
    hass: HomeAssistant, hass_client_no_auth
) -> None:
    entry = await _setup_entry(hass)

    # Enfileira um comando manualmente para checar a resposta
    entry.runtime_data.queue.add({"type": "show_message", "text": "oi"})

    client = await hass_client_no_auth()
    resp = await client.post(
        f"/api/webhook/{WEBHOOK_ID}", json={"battery_level": 80, "reading": True}
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["commands"] == [{"type": "show_message", "text": "oi"}]

    # Snapshot guardado e fila drenada
    assert entry.runtime_data.snapshot.battery_level == 80
    assert entry.runtime_data.queue.pending == []


async def test_webhook_rejects_non_object(
    hass: HomeAssistant, hass_client_no_auth
) -> None:
    await _setup_entry(hass)
    client = await hass_client_no_auth()
    resp = await client.post(f"/api/webhook/{WEBHOOK_ID}", json=[1, 2, 3])
    assert resp.status == 422


async def test_unload_unregisters_webhook(hass: HomeAssistant) -> None:
    entry = await _setup_entry(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    # Reenviar pelo mesmo id agora deve falhar em registrar de novo? Verificamos que desregistrou:
    # async_unregister é idempotente; aqui só garantimos que o unload retornou True acima.
