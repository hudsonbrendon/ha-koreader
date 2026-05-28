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
        snapshot = entry.runtime_data.snapshot
        if snapshot is not None and snapshot.device_model:
            model = snapshot.device_model
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="KOReader",
            manufacturer="KOReader",
            model=model,
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
        snapshot = self._snapshot
        if snapshot is not None and snapshot.device_model and self._attr_device_info is not None:
            self._attr_device_info["model"] = snapshot.device_model
        self.async_write_ha_state()
