"""Constantes da integração KOReader (HA-specific). Protocol logic lives in pykoreader."""

from __future__ import annotations

DOMAIN = "koreader"


def signal_update(entry_id: str) -> str:
    """Sinal disparado quando chega telemetria nova para uma entry."""
    return f"{DOMAIN}_update_{entry_id}"


# Serviços
SERVICE_SHOW_MESSAGE = "show_message"
ATTR_MESSAGE = "message"
ATTR_TIMEOUT = "timeout"
SERVICE_GO_TO_PAGE = "go_to_page"
ATTR_PAGE = "page"
