"""Entidade base da integração KOReader."""

from __future__ import annotations

from pykoreader import Snapshot

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, signal_update


class KOReaderEntity(Entity):
    """Base: ligada ao device da entry e atualizada por dispatcher."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry) -> None:
        self._entry = entry
        model = "KOReader"
        sw_version = None
        snapshot = entry.runtime_data.snapshot
        if snapshot is not None:
            if snapshot.device_model:
                model = snapshot.device_model
            sw_version = snapshot.koreader_version
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="KOReader",
            manufacturer="KOReader",
            model=model,
            sw_version=sw_version,
        )

    @property
    def _snapshot(self) -> Snapshot | None:
        return self._entry.runtime_data.snapshot

    @property
    def available(self) -> bool:
        return self._snapshot is not None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_update(self._entry.entry_id), self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        # model / sw_version updates land in the device registry from the webhook
        # handler (_async_update_device); here we only refresh the entity state.
        self.async_write_ha_state()
