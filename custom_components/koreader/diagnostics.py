"""Diagnostics da integração KOReader: despeja o snapshot e a fila de comandos."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant

from . import KOReaderConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: KOReaderConfigEntry
) -> dict[str, Any]:
    """Retorna o estado em memória da entry para download de diagnóstico."""
    runtime = entry.runtime_data
    snapshot = runtime.snapshot
    return {
        "snapshot": asdict(snapshot) if snapshot is not None else None,
        "last_update": (
            runtime.last_update.isoformat() if runtime.last_update else None
        ),
        "pending_commands": runtime.queue.pending,
    }
