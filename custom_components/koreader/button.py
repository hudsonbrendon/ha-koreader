"""Buttons: enfileiram comandos discretos para o KOReader no próximo check-in."""

from __future__ import annotations

from pykoreader import commands as kcmd

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KOReaderEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            KOReaderSyncButton(entry),
            KOReaderNextPageButton(entry),
            KOReaderPrevPageButton(entry),
            KOReaderRefreshButton(entry),
        ]
    )


class KOReaderButton(KOReaderEntity, ButtonEntity):
    """Base dos botões: sempre disponível (enfileira comandos sem telemetria prévia)."""

    @property
    def available(self) -> bool:
        return True


class KOReaderSyncButton(KOReaderButton):
    _attr_name = "Force sync"
    _attr_icon = "mdi:sync"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_force_sync"

    async def async_press(self) -> None:
        self._entry.runtime_data.queue.add(kcmd.sync_now())


class KOReaderNextPageButton(KOReaderButton):
    _attr_name = "Next page"
    _attr_icon = "mdi:chevron-right"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_next_page"

    async def async_press(self) -> None:
        self._entry.runtime_data.queue.add(kcmd.page_turn(1))


class KOReaderPrevPageButton(KOReaderButton):
    _attr_name = "Previous page"
    _attr_icon = "mdi:chevron-left"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_prev_page"

    async def async_press(self) -> None:
        self._entry.runtime_data.queue.add(kcmd.page_turn(-1))


class KOReaderRefreshButton(KOReaderButton):
    _attr_name = "Refresh screen"
    _attr_icon = "mdi:refresh"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_refresh"

    async def async_press(self) -> None:
        self._entry.runtime_data.queue.add(kcmd.refresh())
