"""Testa os eventos disparados em transições de telemetria."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from custom_components.koreader.const import (
    ATTR_EVENT_TYPE,
    DOMAIN,
    EVENT_BOOK_CHANGED,
    EVENT_BOOK_FINISHED,
    EVENT_HIGHLIGHT_ADDED,
    EVENT_KOREADER,
    EVENT_SESSION_ENDED,
    EVENT_SESSION_STARTED,
)

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _post(client, **payload):
    resp = await client.post(f"/api/webhook/{WEBHOOK_ID}", json=payload)
    assert resp.status == 200


def _types(events):
    return [e.data[ATTR_EVENT_TYPE] for e in events]


async def test_session_started_and_ended(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    events = async_capture_events(hass, EVENT_KOREADER)

    await _post(client, reading=False)
    await _post(client, reading=True)
    await _post(client, reading=False)
    await hass.async_block_till_done()

    types = _types(events)
    assert EVENT_SESSION_STARTED in types
    assert EVENT_SESSION_ENDED in types


async def test_highlight_added_on_count_increase(
    hass: HomeAssistant, hass_client_no_auth
):
    await _setup(hass)
    client = await hass_client_no_auth()
    events = async_capture_events(hass, EVENT_KOREADER)

    await _post(client, annotations_count=2)
    await _post(client, annotations_count=5)
    await hass.async_block_till_done()

    assert EVENT_HIGHLIGHT_ADDED in _types(events)


async def test_book_finished_on_progress_100(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    events = async_capture_events(hass, EVENT_KOREADER)

    await _post(client, progress_percent=80)
    await _post(client, progress_percent=100)
    await hass.async_block_till_done()

    assert EVENT_BOOK_FINISHED in _types(events)


async def test_book_changed_on_title_change(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    events = async_capture_events(hass, EVENT_KOREADER)

    await _post(client, book_title="Duna")
    await _post(client, book_title="Fundação")
    await hass.async_block_till_done()

    assert EVENT_BOOK_CHANGED in _types(events)


async def test_no_spurious_events_on_first_snapshot(
    hass: HomeAssistant, hass_client_no_auth
):
    await _setup(hass)
    client = await hass_client_no_auth()
    events = async_capture_events(hass, EVENT_KOREADER)

    # Primeiro snapshot já lendo não deve disparar session_ended nem book_changed.
    await _post(client, reading=True, book_title="Duna", progress_percent=10)
    await hass.async_block_till_done()

    assert EVENT_SESSION_ENDED not in _types(events)
    assert EVENT_BOOK_CHANGED not in _types(events)
    assert EVENT_BOOK_FINISHED not in _types(events)
