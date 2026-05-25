"""Switch: liga/desliga o WiFi do Kindle (afeta o próprio canal — use com cuidado)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_SET_FRONTLIGHT_POWER, CMD_SET_WIFI, queue_command
from .entity import KOReaderEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [KOReaderWifiSwitch(entry), KOReaderFrontlightSwitch(entry)]
    )


class KOReaderWifiSwitch(KOReaderEntity, SwitchEntity):
    _attr_name = "WiFi"
    _attr_icon = "mdi:wifi"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_wifi"

    @property
    def available(self) -> bool:
        # Control entities are always available: they enqueue commands even before
        # the first webhook payload arrives.
        return True

    @property
    def is_on(self) -> bool:
        return bool(self._payload.get("wifi_connected"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        queue_command(self._entry.runtime_data, {"type": CMD_SET_WIFI, "value": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        queue_command(self._entry.runtime_data, {"type": CMD_SET_WIFI, "value": False})


class KOReaderFrontlightSwitch(KOReaderEntity, SwitchEntity):
    _attr_name = "Frontlight"
    _attr_icon = "mdi:lightbulb"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_frontlight_power"

    @property
    def available(self) -> bool:
        # Control entities are always available: they enqueue commands even before
        # the first webhook payload arrives.
        return True

    @property
    def is_on(self) -> bool:
        return bool(self._payload.get("frontlight_on"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        queue_command(
            self._entry.runtime_data,
            {"type": CMD_SET_FRONTLIGHT_POWER, "value": True},
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        queue_command(
            self._entry.runtime_data,
            {"type": CMD_SET_FRONTLIGHT_POWER, "value": False},
        )
