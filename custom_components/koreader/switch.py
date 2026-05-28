"""Switch: liga/desliga o WiFi e o frontlight do Kindle."""

from __future__ import annotations

from typing import Any

from pykoreader import commands as kcmd

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KOReaderEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([KOReaderWifiSwitch(entry), KOReaderFrontlightSwitch(entry)])


class KOReaderWifiSwitch(KOReaderEntity, SwitchEntity):
    _attr_name = "WiFi"
    _attr_icon = "mdi:wifi"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_wifi"

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        snapshot = self._snapshot
        return bool(snapshot is not None and snapshot.wifi_connected)

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._entry.runtime_data.queue.add(kcmd.set_wifi(True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._entry.runtime_data.queue.add(kcmd.set_wifi(False))


class KOReaderFrontlightSwitch(KOReaderEntity, SwitchEntity):
    _attr_name = "Frontlight"
    _attr_icon = "mdi:lightbulb"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_frontlight_power"

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        snapshot = self._snapshot
        return bool(snapshot is not None and snapshot.frontlight_on)

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._entry.runtime_data.queue.add(kcmd.set_frontlight_power(True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._entry.runtime_data.queue.add(kcmd.set_frontlight_power(False))
