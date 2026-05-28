"""Number: controla a intensidade do frontlight e o warmth do Kindle."""

from __future__ import annotations

from pykoreader import commands as kcmd

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KOReaderEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([KOReaderFrontlight(entry), KOReaderWarmth(entry)])


class _KOReaderSliderBase(KOReaderEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    @property
    def available(self) -> bool:
        # Control entities are always available: they enqueue commands even before
        # the first webhook payload arrives.
        return True


class KOReaderFrontlight(_KOReaderSliderBase):
    _attr_name = "Frontlight"
    _attr_icon = "mdi:brightness-6"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_frontlight"

    @property
    def native_value(self) -> float | None:
        snapshot = self._snapshot
        value = None if snapshot is None else snapshot.frontlight
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        self._entry.runtime_data.queue.add(kcmd.set_frontlight(int(value)))


class KOReaderWarmth(_KOReaderSliderBase):
    _attr_name = "Warmth"
    _attr_icon = "mdi:weather-sunny"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_warmth"

    @property
    def native_value(self) -> float | None:
        snapshot = self._snapshot
        value = None if snapshot is None else snapshot.warmth
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        self._entry.runtime_data.queue.add(kcmd.set_warmth(int(value)))
