"""Binary sensors do KOReader."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pykoreader import Snapshot

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import CONNECTIVITY_TIMEOUT
from .entity import KOReaderEntity


@dataclass(frozen=True, kw_only=True)
class KOReaderBinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[Snapshot], bool | None]


BINARY_SENSORS: tuple[KOReaderBinarySensorEntityDescription, ...] = (
    KOReaderBinarySensorEntityDescription(
        key="reading",
        name="Reading",
        icon="mdi:book-open-variant",
        value_fn=lambda s: s.reading,
    ),
    KOReaderBinarySensorEntityDescription(
        key="charging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda s: s.is_charging,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    entities: list[BinarySensorEntity] = [
        KOReaderBinarySensor(entry, desc) for desc in BINARY_SENSORS
    ]
    entities.append(KOReaderConnectivity(entry))
    async_add_entities(entities)


class KOReaderBinarySensor(KOReaderEntity, BinarySensorEntity):
    entity_description: KOReaderBinarySensorEntityDescription

    def __init__(self, entry, description: KOReaderBinarySensorEntityDescription) -> None:
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        snapshot = self._snapshot
        if snapshot is None:
            return None
        return self.entity_description.value_fn(snapshot)


class KOReaderConnectivity(KOReaderEntity, BinarySensorEntity):
    """Online enquanto houve um check-in dentro da janela de timeout.

    E-ink dorme, então sempre disponível: o próprio estado (on/off) comunica se o
    dispositivo está em contato. Reavalia periodicamente para cair para offline
    mesmo sem novos check-ins.
    """

    _attr_name = "Status"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_connectivity"

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        last = self._entry.runtime_data.last_update
        if last is None:
            return False
        return dt_util.utcnow() - last <= CONNECTIVITY_TIMEOUT

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def _recheck(_now) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_time_interval(self.hass, _recheck, CONNECTIVITY_TIMEOUT)
        )
