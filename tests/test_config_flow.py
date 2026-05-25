"""Testa o config flow por webhook."""

import sys
import types

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.koreader.const import DOMAIN


async def test_create_entry_generates_webhook_id(
    hass: HomeAssistant, monkeypatch
) -> None:
    """O flow cria uma entry com um webhook_id gerado."""
    # GOTCHA (documentado no plano): register_webhook_flow exige uma URL externa
    # para gerar a URL do webhook; o HA de teste não tem uma. Definimos uma antes
    # do flow para que webhook.async_generate_url funcione.
    await hass.config.async_update(
        external_url="https://example.com", internal_url="https://example.com"
    )

    # O passo do flow faz um import local de homeassistant.components.cloud, que
    # nesta versão do HA puxa uma cadeia de deps opcionais (tts/ffmpeg/vad) não
    # incluídas no harness de teste. Como não há assinatura de cloud, o flow segue
    # pelo caminho async_generate_url. Injetamos um stub leve de cloud só para o
    # import resolver (a função abaixo retorna False -> caminho sem cloudhook).
    if "homeassistant.components.cloud" not in sys.modules:
        cloud_stub = types.ModuleType("homeassistant.components.cloud")
        cloud_stub.async_active_subscription = lambda hass: False  # noqa: ARG005
        cloud_stub.async_create_cloudhook = None
        cloud_stub.async_is_connected = lambda hass: False  # noqa: ARG005
        monkeypatch.setitem(
            sys.modules, "homeassistant.components.cloud", cloud_stub
        )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert CONF_WEBHOOK_ID in result["result"].data
    assert result["result"].data[CONF_WEBHOOK_ID]
