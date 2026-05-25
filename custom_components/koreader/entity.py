"""Entidade base da integração KOReader."""

from __future__ import annotations

from typing import Any

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
        model = entry.runtime_data.data.get("device_model") or "KOReader"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="KOReader",
            manufacturer="KOReader",
            model=model,
        )

    @property
    def _payload(self) -> dict[str, Any]:
        return self._entry.runtime_data.data

    @property
    def available(self) -> bool:
        return bool(self._payload)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_update(self._entry.entry_id), self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        # Atualiza o model do device caso tenha chegado agora.
        model = self._payload.get("device_model")
        if model and self._attr_device_info is not None:
            self._attr_device_info["model"] = model
        self.async_write_ha_state()
