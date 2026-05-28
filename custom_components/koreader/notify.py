"""Notify: envia uma mensagem para a tela do KOReader como alvo de notificação."""

from __future__ import annotations

from pykoreader import commands as kcmd

from homeassistant.components.notify import NotifyEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KOReaderEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([KOReaderNotify(entry)])


class KOReaderNotify(KOReaderEntity, NotifyEntity):
    """Mostra a mensagem na tela do Kindle no próximo check-in."""

    _attr_name = "Notify"
    _attr_icon = "mdi:message-text"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_notify"

    @property
    def available(self) -> bool:
        # Enfileira comandos mesmo antes do primeiro check-in.
        return True

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        self._entry.runtime_data.queue.add(kcmd.show_message(message))
