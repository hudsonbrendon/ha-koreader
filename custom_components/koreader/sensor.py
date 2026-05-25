"""Sensores read-only do KOReader."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KOReaderEntity


@dataclass(frozen=True, kw_only=True)
class KOReaderSensorEntityDescription(SensorEntityDescription):
    """Descrição de um sensor, com função que extrai o valor do snapshot."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[KOReaderSensorEntityDescription, ...] = (
    KOReaderSensorEntityDescription(
        key="battery",
        name="Battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("battery_level"),
    ),
    KOReaderSensorEntityDescription(
        key="book_title",
        name="Book title",
        icon="mdi:book",
        value_fn=lambda d: d.get("book_title"),
    ),
    KOReaderSensorEntityDescription(
        key="book_author",
        name="Book author",
        icon="mdi:account-edit",
        value_fn=lambda d: d.get("book_author"),
    ),
    KOReaderSensorEntityDescription(
        key="progress",
        name="Progress",
        icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("progress_percent"),
    ),
    KOReaderSensorEntityDescription(
        key="current_page",
        name="Current page",
        icon="mdi:book-open-page-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("current_page"),
    ),
    KOReaderSensorEntityDescription(
        key="total_pages",
        name="Total pages",
        icon="mdi:book-open-page-variant",
        value_fn=lambda d: d.get("total_pages"),
    ),
    KOReaderSensorEntityDescription(
        key="chapter",
        name="Chapter",
        icon="mdi:format-list-bulleted",
        value_fn=lambda d: d.get("chapter"),
    ),
    KOReaderSensorEntityDescription(
        key="reading_time_today",
        name="Reading time today",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.get("reading_time_today_min"),
    ),
    KOReaderSensorEntityDescription(
        key="pages_today",
        name="Pages read today",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.get("pages_read_today"),
    ),
    KOReaderSensorEntityDescription(
        key="session_time",
        name="Session time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("session_time_min"),
    ),
    KOReaderSensorEntityDescription(
        key="reading_speed",
        name="Reading speed",
        icon="mdi:speedometer",
        native_unit_of_measurement="pages/h",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("reading_speed_pph"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(KOReaderSensor(entry, desc) for desc in SENSORS)


class KOReaderSensor(KOReaderEntity, SensorEntity):
    """Um sensor read-only do KOReader."""

    entity_description: KOReaderSensorEntityDescription

    def __init__(self, entry, description: KOReaderSensorEntityDescription) -> None:
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._payload)
