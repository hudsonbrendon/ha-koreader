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
            KOReaderNextChapterButton(entry),
            KOReaderPrevChapterButton(entry),
            KOReaderToggleBookmarkButton(entry),
            KOReaderSuspendButton(entry),
            KOReaderRestartButton(entry),
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


class KOReaderNextChapterButton(KOReaderButton):
    _attr_name = "Next chapter"
    _attr_icon = "mdi:chevron-double-right"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_next_chapter"

    async def async_press(self) -> None:
        self._entry.runtime_data.queue.add(kcmd.goto_chapter(1))


class KOReaderPrevChapterButton(KOReaderButton):
    _attr_name = "Previous chapter"
    _attr_icon = "mdi:chevron-double-left"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_prev_chapter"

    async def async_press(self) -> None:
        self._entry.runtime_data.queue.add(kcmd.goto_chapter(-1))


class KOReaderToggleBookmarkButton(KOReaderButton):
    _attr_name = "Toggle bookmark"
    _attr_icon = "mdi:bookmark-outline"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_toggle_bookmark"

    async def async_press(self) -> None:
        self._entry.runtime_data.queue.add(kcmd.toggle_bookmark())


class KOReaderSuspendButton(KOReaderButton):
    _attr_name = "Suspend"
    _attr_icon = "mdi:sleep"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_suspend"

    async def async_press(self) -> None:
        self._entry.runtime_data.queue.add(kcmd.suspend())


class KOReaderRestartButton(KOReaderButton):
    _attr_name = "Restart"
    _attr_icon = "mdi:restart"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_restart"

    async def async_press(self) -> None:
        self._entry.runtime_data.queue.add(kcmd.restart())
