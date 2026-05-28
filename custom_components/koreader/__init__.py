"""Integração KOReader: recebe telemetria por webhook e devolve comandos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from http import HTTPStatus

import voluptuous as vol
from aiohttp import web
from pykoreader import CommandQueue, Snapshot, commands as kcmd, parse_payload

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_WEBHOOK_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import (
    config_entry_flow,
    config_validation as cv,
    device_registry as dr,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DEVICE_ID,
    ATTR_EVENT_TYPE,
    ATTR_MESSAGE,
    ATTR_PAGE,
    ATTR_PERCENT,
    ATTR_TIMEOUT,
    DOMAIN,
    EVENT_BOOK_CHANGED,
    EVENT_BOOK_FINISHED,
    EVENT_HIGHLIGHT_ADDED,
    EVENT_KOREADER,
    EVENT_SESSION_ENDED,
    EVENT_SESSION_STARTED,
    SERVICE_GO_TO_PAGE,
    SERVICE_GO_TO_PERCENTAGE,
    SERVICE_SHOW_MESSAGE,
    signal_update,
)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NOTIFY,
]

SHOW_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_TIMEOUT): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
    }
)

GO_TO_PAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PAGE): vol.All(vol.Coerce(int), vol.Range(min=1)),
    }
)

GO_TO_PERCENTAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PERCENT): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=100)
        ),
    }
)


@dataclass
class KOReaderRuntimeData:
    """Estado em memória de uma config entry."""

    snapshot: Snapshot | None = None
    queue: CommandQueue = field(default_factory=CommandQueue)
    last_update: datetime | None = None


type KOReaderConfigEntry = ConfigEntry[KOReaderRuntimeData]


async def handle_webhook(
    entry: KOReaderConfigEntry,
    hass: HomeAssistant,
    webhook_id: str,
    request: web.Request,
) -> web.Response:
    """Recebe o snapshot do KOReader, guarda, atualiza entidades e devolve comandos."""
    try:
        payload = await request.json()
    except ValueError:
        return web.Response(status=HTTPStatus.BAD_REQUEST)

    try:
        snapshot = parse_payload(payload)
    except ValueError:
        return web.Response(status=HTTPStatus.UNPROCESSABLE_ENTITY)

    runtime = entry.runtime_data
    pending = runtime.queue.drain()
    previous = runtime.snapshot
    runtime.snapshot = snapshot
    runtime.last_update = dt_util.utcnow()
    _async_update_device(hass, entry, snapshot)
    _fire_transition_events(hass, entry, previous, snapshot)
    async_dispatcher_send(hass, signal_update(entry.entry_id))
    return web.json_response({"commands": pending})


@callback
def _async_update_device(
    hass: HomeAssistant, entry: KOReaderConfigEntry, snapshot: Snapshot
) -> None:
    """Reflete model/sw_version do snapshot no device registry (mudanças vêm depois do setup)."""
    if not (snapshot.device_model or snapshot.koreader_version):
        return
    registry = dr.async_get(hass)
    device = registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    if device is None:
        return
    kwargs: dict[str, str] = {}
    if snapshot.device_model and device.model != snapshot.device_model:
        kwargs["model"] = snapshot.device_model
    if snapshot.koreader_version and device.sw_version != snapshot.koreader_version:
        kwargs["sw_version"] = snapshot.koreader_version
    if kwargs:
        registry.async_update_device(device.id, **kwargs)


@callback
def _fire_transition_events(
    hass: HomeAssistant,
    entry: KOReaderConfigEntry,
    previous: Snapshot | None,
    current: Snapshot,
) -> None:
    """Dispara eventos no barramento conforme o estado muda entre snapshots."""
    fired: list[str] = []

    if previous is not None:
        if not previous.reading and current.reading:
            fired.append(EVENT_SESSION_STARTED)
        elif previous.reading and not current.reading:
            fired.append(EVENT_SESSION_ENDED)

        if (
            previous.book_title
            and current.book_title
            and previous.book_title != current.book_title
        ):
            fired.append(EVENT_BOOK_CHANGED)
    elif not previous and current.reading:
        fired.append(EVENT_SESSION_STARTED)

    prev_progress = previous.progress_percent if previous else None
    if current.progress_percent is not None and current.progress_percent >= 100 and (
        prev_progress is None or prev_progress < 100
    ):
        fired.append(EVENT_BOOK_FINISHED)

    prev_count = (previous.annotations_count if previous else None) or 0
    if current.annotations_count is not None and current.annotations_count > prev_count:
        fired.append(EVENT_HIGHLIGHT_ADDED)

    if not fired:
        return

    device = dr.async_get(hass).async_get_device(
        identifiers={(DOMAIN, entry.entry_id)}
    )
    device_id = device.id if device else None
    for event_type in fired:
        hass.bus.async_fire(
            EVENT_KOREADER,
            {
                ATTR_EVENT_TYPE: event_type,
                ATTR_DEVICE_ID: device_id,
                "entry_id": entry.entry_id,
            },
        )


async def async_setup_entry(hass: HomeAssistant, entry: KOReaderConfigEntry) -> bool:
    """Configura uma entry: webhook + plataformas + serviço."""
    entry.runtime_data = KOReaderRuntimeData()

    webhook.async_register(
        hass,
        DOMAIN,
        "KOReader",
        entry.data[CONF_WEBHOOK_ID],
        partial(handle_webhook, entry),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KOReaderConfigEntry) -> bool:
    """Descarrega uma entry."""
    webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# Limpa o webhook registrado quando a config entry é removida.
async_remove_entry = config_entry_flow.webhook_async_remove_entry


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    """Registra os serviços koreader.show_message e koreader.go_to_page (uma vez)."""
    if hass.services.has_service(DOMAIN, SERVICE_SHOW_MESSAGE):
        return

    async def _show_message(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is ConfigEntryState.LOADED:
                entry.runtime_data.queue.add(
                    kcmd.show_message(call.data[ATTR_MESSAGE], call.data.get(ATTR_TIMEOUT))
                )

    async def _go_to_page(call: ServiceCall) -> None:
        page = call.data[ATTR_PAGE]
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is ConfigEntryState.LOADED:
                entry.runtime_data.queue.add(kcmd.goto_page(page))

    async def _go_to_percentage(call: ServiceCall) -> None:
        percent = call.data[ATTR_PERCENT]
        queued = False
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is not ConfigEntryState.LOADED:
                continue
            snapshot = entry.runtime_data.snapshot
            total_pages = None if snapshot is None else snapshot.total_pages
            if not total_pages:
                continue
            page = max(1, round(percent / 100 * total_pages))
            entry.runtime_data.queue.add(kcmd.goto_page(page))
            queued = True
        if not queued:
            raise ServiceValidationError(
                "KOReader não tem total de páginas conhecido ainda; "
                "aguarde um check-in ou use go_to_page."
            )

    hass.services.async_register(
        DOMAIN, SERVICE_SHOW_MESSAGE, _show_message, schema=SHOW_MESSAGE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_GO_TO_PAGE, _go_to_page, schema=GO_TO_PAGE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GO_TO_PERCENTAGE,
        _go_to_percentage,
        schema=GO_TO_PERCENTAGE_SCHEMA,
    )
