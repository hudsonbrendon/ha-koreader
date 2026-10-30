"""Serviços da integração KOReader: enfileiram comandos para o próximo check-in."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from pykoreader import commands as kcmd
import voluptuous as vol

from .const import (
    ATTR_MESSAGE,
    ATTR_PAGE,
    ATTR_PERCENT,
    ATTR_TIMEOUT,
    DOMAIN,
    SERVICE_GO_TO_PAGE,
    SERVICE_GO_TO_PERCENTAGE,
    SERVICE_SHOW_MESSAGE,
)

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


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Registra os serviços koreader.show_message, go_to_page e go_to_percentage."""

    async def _show_message(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is ConfigEntryState.LOADED:
                entry.runtime_data.queue.add(
                    kcmd.show_message(
                        call.data[ATTR_MESSAGE], call.data.get(ATTR_TIMEOUT)
                    )
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
