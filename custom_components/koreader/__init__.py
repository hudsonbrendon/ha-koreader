"""Integração KOReader: recebe telemetria por webhook e devolve comandos."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from http import HTTPStatus
from typing import Any

import voluptuous as vol
from aiohttp import web

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_WEBHOOK_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_entry_flow, config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    ATTR_MESSAGE,
    ATTR_TIMEOUT,
    CMD_SHOW_MESSAGE,
    DOMAIN,
    SERVICE_SHOW_MESSAGE,
    signal_update,
)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BUTTON,
]

SHOW_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_TIMEOUT): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
    }
)


@dataclass
class KOReaderRuntimeData:
    """Estado em memória de uma config entry."""

    data: dict[str, Any] = field(default_factory=dict)
    commands: list[dict[str, Any]] = field(default_factory=list)


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

    if not isinstance(payload, dict):
        return web.Response(status=HTTPStatus.UNPROCESSABLE_ENTITY)

    runtime = entry.runtime_data
    runtime.data = payload
    async_dispatcher_send(hass, signal_update(entry.entry_id))

    commands = runtime.commands
    runtime.commands = []
    return web.json_response({"commands": commands})


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


async_remove_entry = config_entry_flow.webhook_async_remove_entry


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    """Registra o serviço koreader.show_message (uma vez)."""
    if hass.services.has_service(DOMAIN, SERVICE_SHOW_MESSAGE):
        return

    async def _show_message(call: ServiceCall) -> None:
        command: dict[str, Any] = {"type": CMD_SHOW_MESSAGE, "text": call.data[ATTR_MESSAGE]}
        if ATTR_TIMEOUT in call.data:
            command["timeout"] = call.data[ATTR_TIMEOUT]
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is ConfigEntryState.LOADED:
                entry.runtime_data.commands.append(dict(command))

    hass.services.async_register(
        DOMAIN, SERVICE_SHOW_MESSAGE, _show_message, schema=SHOW_MESSAGE_SCHEMA
    )
