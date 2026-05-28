"""Sensores read-only do KOReader."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from pykoreader import Snapshot

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import KOReaderEntity


@dataclass(frozen=True, kw_only=True)
class KOReaderSensorEntityDescription(SensorEntityDescription):
    """Descrição de um sensor, com função que extrai o valor do snapshot."""

    value_fn: Callable[[Snapshot], Any]


SENSORS: tuple[KOReaderSensorEntityDescription, ...] = (
    KOReaderSensorEntityDescription(
        key="battery", name="Battery", device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.battery_level),
    KOReaderSensorEntityDescription(
        key="book_title", name="Book title", icon="mdi:book",
        value_fn=lambda s: s.book_title),
    KOReaderSensorEntityDescription(
        key="book_author", name="Book author", icon="mdi:account-edit",
        value_fn=lambda s: s.book_author),
    KOReaderSensorEntityDescription(
        key="progress", name="Progress", icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.progress_percent),
    KOReaderSensorEntityDescription(
        key="current_page", name="Current page", icon="mdi:book-open-page-variant",
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.current_page),
    KOReaderSensorEntityDescription(
        key="total_pages", name="Total pages", icon="mdi:book-open-page-variant",
        value_fn=lambda s: s.total_pages),
    KOReaderSensorEntityDescription(
        key="chapter", name="Chapter", icon="mdi:format-list-bulleted",
        value_fn=lambda s: s.chapter),
    KOReaderSensorEntityDescription(
        key="reading_time_today", name="Reading time today",
        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.TOTAL_INCREASING, value_fn=lambda s: s.reading_time_today_min),
    KOReaderSensorEntityDescription(
        key="pages_today", name="Pages read today", icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING, value_fn=lambda s: s.pages_read_today),
    KOReaderSensorEntityDescription(
        key="session_time", name="Session time", device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES, state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.session_time_min),
    KOReaderSensorEntityDescription(
        key="reading_speed", name="Reading speed", icon="mdi:speedometer",
        native_unit_of_measurement="pages/h", state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.reading_speed_pph),
    KOReaderSensorEntityDescription(
        key="pages_left", name="Pages left", icon="mdi:book-arrow-right-outline",
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.pages_left),
    KOReaderSensorEntityDescription(
        key="pages_left_chapter", name="Pages left in chapter",
        icon="mdi:book-arrow-right-outline", state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.pages_left_chapter),
    KOReaderSensorEntityDescription(
        key="time_to_finish_book", name="Time to finish book",
        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.time_to_finish_book_min),
    KOReaderSensorEntityDescription(
        key="time_to_finish_chapter", name="Time to finish chapter",
        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.time_to_finish_chapter_min),
    KOReaderSensorEntityDescription(
        key="book_format", name="Book format", icon="mdi:file-document-outline",
        value_fn=lambda s: s.book_format),
    KOReaderSensorEntityDescription(
        key="book_language", name="Book language", icon="mdi:translate",
        value_fn=lambda s: s.book_language),
    KOReaderSensorEntityDescription(
        key="book_series", name="Book series", icon="mdi:bookshelf",
        value_fn=lambda s: s.book_series),
    KOReaderSensorEntityDescription(
        key="total_time", name="Total reading time", device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES, state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda s: s.total_time_min),
    KOReaderSensorEntityDescription(
        key="annotations", name="Annotations", icon="mdi:marker",
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.annotations_count),
    KOReaderSensorEntityDescription(
        key="highlights", name="Highlights", icon="mdi:marker",
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.highlights_count),
    KOReaderSensorEntityDescription(
        key="notes", name="Notes", icon="mdi:note-edit-outline",
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.notes_count),
)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    entities: list[SensorEntity] = [KOReaderSensor(entry, desc) for desc in SENSORS]
    entities.append(KOReaderLastCheckin(entry))
    entities.append(KOReaderFinishDate(entry))
    async_add_entities(entities)


class KOReaderSensor(KOReaderEntity, SensorEntity):
    """Um sensor read-only do KOReader."""

    entity_description: KOReaderSensorEntityDescription

    def __init__(self, entry, description: KOReaderSensorEntityDescription) -> None:
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        snapshot = self._snapshot
        if snapshot is None:
            return None
        return self.entity_description.value_fn(snapshot)


class KOReaderLastCheckin(KOReaderEntity, SensorEntity):
    """Quando o KOReader enviou telemetria pela última vez (relógio do HA)."""

    _attr_name = "Last check-in"
    _attr_icon = "mdi:clock-check-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_last_checkin"

    @property
    def native_value(self) -> datetime | None:
        return self._entry.runtime_data.last_update


class KOReaderFinishDate(KOReaderEntity, SensorEntity):
    """Data estimada de término do livro no ritmo atual de leitura."""

    _attr_name = "Estimated finish date"
    _attr_icon = "mdi:book-clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_finish_date"

    @property
    def native_value(self) -> datetime | None:
        snapshot = self._snapshot
        if snapshot is None or snapshot.time_to_finish_book_min is None:
            return None
        return dt_util.utcnow() + timedelta(minutes=snapshot.time_to_finish_book_min)
