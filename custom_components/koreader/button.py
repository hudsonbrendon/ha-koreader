"""Button: pede ao KOReader um envio/sync imediato no próximo evento."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_SYNC_NOW
from .entity import KOReaderEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([KOReaderSyncButton(entry)])


class KOReaderSyncButton(KOReaderEntity, ButtonEntity):
    _attr_name = "Force sync"
    _attr_icon = "mdi:sync"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_force_sync"

    @property
    def available(self) -> bool:
        # Buttons are always available: they enqueue commands regardless of
        # whether a webhook payload has been received yet.
        return True

    async def async_press(self) -> None:
        self._entry.runtime_data.commands.append({"type": CMD_SYNC_NOW})
