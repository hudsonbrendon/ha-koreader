"""Number: controla a intensidade do frontlight do Kindle."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_SET_FRONTLIGHT
from .entity import KOReaderEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([KOReaderFrontlight(entry)])


class KOReaderFrontlight(KOReaderEntity, NumberEntity):
    """Slider de frontlight (lê o valor atual, controla no próximo check-in)."""

    _attr_name = "Frontlight"
    _attr_icon = "mdi:brightness-6"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_frontlight"

    @property
    def available(self) -> bool:
        # Control entities are always available: they enqueue commands even before
        # the first webhook payload arrives.
        return True

    @property
    def native_value(self) -> float | None:
        value = self._payload.get("frontlight")
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        self._entry.runtime_data.commands.append(
            {"type": CMD_SET_FRONTLIGHT, "value": int(value)}
        )
        # Otimista: reflete já, será confirmado no próximo snapshot.
        self._entry.runtime_data.data["frontlight"] = int(value)
        self.async_write_ha_state()
