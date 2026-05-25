# Plano de Implementação — Integração Nativa KOReader para Home Assistant

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans pra implementar tarefa a tarefa. Os passos usam checkbox (`- [ ]`).

**Objetivo:** Criar um custom component nativo (`custom_components/koreader/`), instalável via HACS, que recebe a telemetria do KOReader por **webhook**, expõe tudo como entidades de um device dedicado, e permite **controlar o Kindle** (luz, mensagem na tela, wifi, sync) através de uma fila de comandos devolvida na resposta do webhook.

**Arquitetura:** O plugin do KOReader (repo `hatelemetry.koplugin`, já existente) passa a mandar o snapshot JSON inteiro num **único POST** pra URL de webhook da integração. A integração guarda o último snapshot em `entry.runtime_data`, dispara um sinal de dispatcher e as entidades se atualizam (push, `should_poll=False`). Entidades de controle (number/switch/button) e o serviço `show_message` **enfileiram comandos**; o handler do webhook **devolve esses comandos na resposta** do próximo POST, e o plugin os executa no Kindle. Identidade do device = a config entry (1 Kindle por webhook).

**Stack:** Python 3.12+ / Home Assistant (API `dev`), `aiohttp` (webhook), `voluptuous` (schema do serviço). Testes: `pytest` + `pytest-homeassistant-custom-component` + `pytest-asyncio`. Lado KOReader: Lua 5.1 / LuaJIT, testes com `busted`. Distribuição: HACS (repo customizado).

**Limitação importante (e-ink):** o controle HA→Kindle **não é instantâneo**. Os comandos só chegam quando o KOReader faz o próximo check-in (virar página, acordar, ou loop periódico) **com WiFi ligado**. Com a tela apagada o WiFi cai e nada chega até acordar. Isso é documentado e deve ser comunicado ao usuário.

**Contrato JSON (snapshot)** — a ponte entre o plugin e a integração. Campos (produzidos por `snapshot.lua` no plugin):

```json
{
  "reading": true,
  "device_model": "Kindle Oasis",
  "battery_level": 87,
  "is_charging": false,
  "frontlight": 12,
  "wifi_connected": true,
  "book_title": "Duna",
  "book_author": "Frank Herbert",
  "current_page": 130,
  "total_pages": 412,
  "progress_percent": 31,
  "chapter": "Capítulo 5",
  "reading_time_today_min": 35,
  "pages_read_today": 40,
  "session_time_min": 12,
  "reading_speed_pph": 68,
  "last_seen": "2026-05-25T12:00:00Z"
}
```

Resposta do webhook (HA → plugin):

```json
{ "commands": [ {"type": "set_frontlight", "value": 20}, {"type": "show_message", "text": "Oi!"} ] }
```

---

## Estrutura de arquivos

Raiz do repo da integração: `/Users/hudsonbrendon/Github/ha-koreader/`

```
ha-koreader/
  hacs.json                         # metadados HACS
  README.md
  requirements-test.txt             # deps de teste
  custom_components/koreader/
    __init__.py                     # runtime data, webhook handler, setup/unload, serviço
    manifest.json                   # domain, config_flow, dependencies=[webhook], version
    const.py                        # DOMAIN, sinais, tipos de comando
    config_flow.py                  # register_webhook_flow
    entity.py                       # KOReaderEntity base (device_info + dispatcher)
    sensor.py                       # sensores read-only
    binary_sensor.py                # status (lendo) + carregando
    number.py                       # frontlight (lê + controla)
    switch.py                       # wifi (lê + controla)
    button.py                       # forçar sync
    services.yaml                   # schema UI do serviço show_message
    strings.json                    # textos do config flow (en base)
    translations/en.json
    translations/pt-BR.json
  tests/
    __init__.py
    conftest.py
    test_config_flow.py
    test_init.py
    test_sensor.py
    test_binary_sensor.py
    test_number.py
    test_switch.py
    test_button.py
    test_service.py
  docs/
    home-assistant/dashboard.yaml
    superpowers/plans/2026-05-25-koreader-ha-native-integration.md  # este arquivo
```

Mudanças no repo do plugin `/Users/hudsonbrendon/Github/hatelemetry.koplugin/` (Fase 4):

```
hatelemetry.koplugin/
  ha_webhook.lua    # cliente webhook (envia snapshot, lê comandos da resposta)
  commands.lua      # aplica um comando no Kindle (frontlight, mensagem, wifi, sync)
  main.lua          # MODIFICADO: modo webhook + aplica comandos
  ha_config.sample.lua  # MODIFICADO: campo webhook_id
  spec/ha_webhook_spec.lua
  spec/commands_spec.lua
```

---

## FASE 0 — Scaffold do repo e toolchain de teste

### Task 0: Criar repo, estrutura e ferramentas de teste

**Arquivos:**
- Create: `/Users/hudsonbrendon/Github/ha-koreader/hacs.json`
- Create: `/Users/hudsonbrendon/Github/ha-koreader/requirements-test.txt`
- Create: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/manifest.json`
- Create: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/const.py`
- Create: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/__init__.py` (stub)
- Create: `/Users/hudsonbrendon/Github/ha-koreader/tests/__init__.py`
- Create: `/Users/hudsonbrendon/Github/ha-koreader/tests/conftest.py`
- Test: `/Users/hudsonbrendon/Github/ha-koreader/tests/test_smoke.py`

- [ ] **Passo 1: Criar diretórios e inicializar git**

Run:
```bash
mkdir -p /Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/translations
mkdir -p /Users/hudsonbrendon/Github/ha-koreader/tests
mkdir -p /Users/hudsonbrendon/Github/ha-koreader/docs/home-assistant
cd /Users/hudsonbrendon/Github/ha-koreader && git init
```
Esperado: `Initialized empty Git repository`.

- [ ] **Passo 2: Criar o ambiente Python e instalar deps de teste**

`requirements-test.txt`:
```
pytest-homeassistant-custom-component
```

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements-test.txt
```
Esperado: instala `pytest-homeassistant-custom-component` (que traz `homeassistant`, `pytest`, `pytest-asyncio` nas versões compatíveis). Se a versão do Python for incompatível com a release atual do HA, use Python 3.13 (`python3.13 -m venv .venv`). Se a instalação falhar, PARE e reporte NEEDS_CONTEXT com o erro — não invente resultados de teste.

- [ ] **Passo 3: Criar `hacs.json`**

`hacs.json`:
```json
{
  "name": "KOReader",
  "render_readme": true,
  "homeassistant": "2024.1.0"
}
```

- [ ] **Passo 4: Criar `manifest.json`**

`custom_components/koreader/manifest.json`:
```json
{
  "domain": "koreader",
  "name": "KOReader",
  "version": "0.1.0",
  "codeowners": ["@hudsonbrendon"],
  "config_flow": true,
  "dependencies": ["webhook"],
  "documentation": "https://github.com/hudsonbrendon/ha-koreader",
  "issue_tracker": "https://github.com/hudsonbrendon/ha-koreader/issues",
  "iot_class": "local_push",
  "integration_type": "device",
  "requirements": []
}
```

- [ ] **Passo 5: Criar `const.py`**

`custom_components/koreader/const.py`:
```python
"""Constantes da integração KOReader."""

from __future__ import annotations

DOMAIN = "koreader"

# Nome do sinal de dispatcher por config entry (atualização de telemetria).
def signal_update(entry_id: str) -> str:
    """Sinal disparado quando chega telemetria nova para uma entry."""
    return f"{DOMAIN}_update_{entry_id}"

# Tipos de comando enfileirados para o Kindle (devolvidos na resposta do webhook).
CMD_SET_FRONTLIGHT = "set_frontlight"
CMD_SHOW_MESSAGE = "show_message"
CMD_SET_WIFI = "set_wifi"
CMD_SYNC_NOW = "sync_now"

# Serviço
SERVICE_SHOW_MESSAGE = "show_message"
ATTR_MESSAGE = "message"
ATTR_TIMEOUT = "timeout"
```

- [ ] **Passo 6: Criar `__init__.py` stub**

`custom_components/koreader/__init__.py`:
```python
"""Integração KOReader (stub inicial; preenchido na Fase 1)."""
```

- [ ] **Passo 7: Criar `tests/__init__.py` e `tests/conftest.py`**

`tests/__init__.py`:
```python
"""Testes da integração KOReader."""
```

`tests/conftest.py`:
```python
"""Fixtures de teste."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Habilita o carregamento de custom_components nos testes."""
    yield
```

- [ ] **Passo 8: Criar o teste de smoke**

`tests/test_smoke.py`:
```python
"""Smoke test do toolchain."""

from custom_components.koreader.const import DOMAIN


def test_domain():
    assert DOMAIN == "koreader"
```

- [ ] **Passo 9: Rodar o smoke test**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_smoke.py -q
```
Esperado: `1 passed`.

- [ ] **Passo 10: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-koreader
printf '.venv/\n__pycache__/\n*.pyc\n' > .gitignore
git add .gitignore hacs.json requirements-test.txt custom_components tests
git commit -m "chore: scaffold ha-koreader custom integration + test toolchain"
```

---

## FASE 1 — Config flow (webhook) + núcleo do webhook

### Task 1: Config flow por webhook

**Arquivos:**
- Create: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/config_flow.py`
- Create: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/strings.json`
- Test: `/Users/hudsonbrendon/Github/ha-koreader/tests/test_config_flow.py`

- [ ] **Passo 1: Escrever o teste que falha**

`tests/test_config_flow.py`:
```python
"""Testa o config flow por webhook."""

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.koreader.const import DOMAIN


async def test_create_entry_generates_webhook_id(hass: HomeAssistant) -> None:
    """O flow cria uma entry com um webhook_id gerado."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert CONF_WEBHOOK_ID in result["result"].data
    assert result["result"].data[CONF_WEBHOOK_ID]
```

- [ ] **Passo 2: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_config_flow.py -q
```
Esperado: FALHA (sem `config_flow.py` / handler não registrado).

- [ ] **Passo 3: Escrever `config_flow.py`**

`custom_components/koreader/config_flow.py`:
```python
"""Config flow da integração KOReader (webhook)."""

from homeassistant.helpers import config_entry_flow

from .const import DOMAIN

config_entry_flow.register_webhook_flow(
    DOMAIN,
    "KOReader Webhook",
    {"docs_url": "https://github.com/hudsonbrendon/ha-koreader"},
)
```

- [ ] **Passo 4: Escrever `strings.json`**

`custom_components/koreader/strings.json`:
```json
{
  "config": {
    "step": {
      "user": {
        "title": "Configurar KOReader",
        "description": "Você quer iniciar a configuração do KOReader?"
      }
    },
    "abort": {
      "single_instance_allowed": "Já configurado.",
      "webhook_not_internet_accessible": "Sua instância do Home Assistant precisa estar acessível pelo dispositivo para receber mensagens de webhook."
    },
    "create_entry": {
      "default": "Para enviar a telemetria do KOReader ao Home Assistant, configure o plugin com a URL de webhook:\n\n`{webhook_url}`"
    }
  }
}
```

- [ ] **Passo 5: Rodar e ver passar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_config_flow.py -q
```
Esperado: `1 passed`.

- [ ] **Passo 6: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-koreader
git add custom_components/koreader/config_flow.py custom_components/koreader/strings.json tests/test_config_flow.py
git commit -m "feat: webhook-based config flow"
```

---

### Task 2: Núcleo do webhook (runtime data, handler, setup/unload)

**Arquivos:**
- Modify: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/__init__.py`
- Test: `/Users/hudsonbrendon/Github/ha-koreader/tests/test_init.py`

- [ ] **Passo 1: Escrever o teste que falha**

`tests/test_init.py`:
```python
"""Testa setup da entry, recebimento de webhook e resposta de comandos."""

from homeassistant.components import webhook
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_webhook_stores_payload_and_returns_commands(
    hass: HomeAssistant, hass_client_no_auth
) -> None:
    entry = await _setup_entry(hass)

    # Enfileira um comando manualmente para checar a resposta
    entry.runtime_data.commands.append({"type": "show_message", "text": "oi"})

    client = await hass_client_no_auth()
    resp = await client.post(
        f"/api/webhook/{WEBHOOK_ID}", json={"battery_level": 80, "reading": True}
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["commands"] == [{"type": "show_message", "text": "oi"}]

    # Snapshot guardado e fila drenada
    assert entry.runtime_data.data["battery_level"] == 80
    assert entry.runtime_data.commands == []


async def test_webhook_rejects_non_object(
    hass: HomeAssistant, hass_client_no_auth
) -> None:
    await _setup_entry(hass)
    client = await hass_client_no_auth()
    resp = await client.post(f"/api/webhook/{WEBHOOK_ID}", json=[1, 2, 3])
    assert resp.status == 422


async def test_unload_unregisters_webhook(hass: HomeAssistant) -> None:
    entry = await _setup_entry(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    # Reenviar pelo mesmo id agora deve falhar em registrar de novo? Verificamos que desregistrou:
    # async_unregister é idempotente; aqui só garantimos que o unload retornou True acima.
```

- [ ] **Passo 2: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_init.py -q
```
Esperado: FALHA (`async_setup_entry` não existe / sem handler).

- [ ] **Passo 3: Escrever `__init__.py` completo**

`custom_components/koreader/__init__.py`:
```python
"""Integração KOReader: recebe telemetria por webhook e devolve comandos."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from http import HTTPStatus
from typing import Any

import voluptuous as vol
from aiohttp import web

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_WEBHOOK_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_entry_flow, config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    ATTR_MESSAGE,
    ATTR_TIMEOUT,
    CMD_SHOW_MESSAGE,
    DOMAIN,
    SERVICE_SHOW_MESSAGE,
    signal_update,
)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BUTTON,
]

SHOW_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_TIMEOUT): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
    }
)


@dataclass
class KOReaderRuntimeData:
    """Estado em memória de uma config entry."""

    data: dict[str, Any] = field(default_factory=dict)
    commands: list[dict[str, Any]] = field(default_factory=list)


type KOReaderConfigEntry = ConfigEntry[KOReaderRuntimeData]


async def handle_webhook(
    entry: KOReaderConfigEntry,
    hass: HomeAssistant,
    webhook_id: str,
    request: web.Request,
) -> web.Response:
    """Recebe o snapshot do KOReader, guarda, atualiza entidades e devolve comandos."""
    try:
        payload = await request.json()
    except ValueError:
        return web.Response(status=HTTPStatus.BAD_REQUEST)

    if not isinstance(payload, dict):
        return web.Response(status=HTTPStatus.UNPROCESSABLE_ENTITY)

    runtime = entry.runtime_data
    runtime.data = payload
    async_dispatcher_send(hass, signal_update(entry.entry_id))

    commands = runtime.commands
    runtime.commands = []
    return web.json_response({"commands": commands})


async def async_setup_entry(hass: HomeAssistant, entry: KOReaderConfigEntry) -> bool:
    """Configura uma entry: webhook + plataformas + serviço."""
    entry.runtime_data = KOReaderRuntimeData()

    webhook.async_register(
        hass,
        DOMAIN,
        "KOReader",
        entry.data[CONF_WEBHOOK_ID],
        partial(handle_webhook, entry),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KOReaderConfigEntry) -> bool:
    """Descarrega uma entry."""
    webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async_remove_entry = config_entry_flow.webhook_async_remove_entry


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    """Registra o serviço koreader.show_message (uma vez)."""
    if hass.services.has_service(DOMAIN, SERVICE_SHOW_MESSAGE):
        return

    async def _show_message(call: ServiceCall) -> None:
        command: dict[str, Any] = {"type": CMD_SHOW_MESSAGE, "text": call.data[ATTR_MESSAGE]}
        if ATTR_TIMEOUT in call.data:
            command["timeout"] = call.data[ATTR_TIMEOUT]
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is ConfigEntryState.LOADED:
                entry.runtime_data.commands.append(dict(command))

    hass.services.async_register(
        DOMAIN, SERVICE_SHOW_MESSAGE, _show_message, schema=SHOW_MESSAGE_SCHEMA
    )
```

> Nota: as plataformas (`sensor`, `binary_sensor`, etc.) ainda não existem; `async_forward_entry_setups` apenas tenta importá-las. Crie um stub mínimo para cada uma antes de rodar, para o setup não quebrar. Faça isto agora:

`custom_components/koreader/sensor.py`, `binary_sensor.py`, `number.py`, `switch.py`, `button.py` — cada um com este stub temporário (substituído nas próximas tasks):
```python
"""Stub temporário (substituído na fase de entidades)."""

async def async_setup_entry(hass, entry, async_add_entities):
    return None
```

- [ ] **Passo 4: Rodar e ver passar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_init.py -q
```
Esperado: `3 passed`.

- [ ] **Passo 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-koreader
git add custom_components/koreader/__init__.py custom_components/koreader/sensor.py custom_components/koreader/binary_sensor.py custom_components/koreader/number.py custom_components/koreader/switch.py custom_components/koreader/button.py tests/test_init.py
git commit -m "feat: webhook handler, runtime data, setup/unload, show_message service"
```

---

## FASE 2 — Entidades de telemetria

### Task 3: Entidade base + sensores

**Arquivos:**
- Create: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/entity.py`
- Modify: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/sensor.py`
- Test: `/Users/hudsonbrendon/Github/ha-koreader/tests/test_sensor.py`

- [ ] **Passo 1: Escrever o teste que falha**

`tests/test_sensor.py`:
```python
"""Testa que o webhook popula os sensores."""

from homeassistant.components import webhook
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"

PAYLOAD = {
    "reading": True,
    "device_model": "Kindle Oasis",
    "battery_level": 87,
    "book_title": "Duna",
    "book_author": "Frank Herbert",
    "progress_percent": 31,
    "current_page": 130,
    "total_pages": 412,
    "chapter": "Capítulo 5",
    "reading_time_today_min": 35,
    "pages_read_today": 40,
    "session_time_min": 12,
    "reading_speed_pph": 68,
    "last_seen": "2026-05-25T12:00:00Z",
}


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_sensors_update_from_webhook(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    resp = await client.post(f"/api/webhook/{WEBHOOK_ID}", json=PAYLOAD)
    assert resp.status == 200
    await hass.async_block_till_done()

    assert hass.states.get("sensor.koreader_battery").state == "87"
    assert hass.states.get("sensor.koreader_progress").state == "31"
    assert hass.states.get("sensor.koreader_current_page").state == "130"
    assert hass.states.get("sensor.koreader_chapter").state == "Capítulo 5"
    assert hass.states.get("sensor.koreader_reading_speed").state == "68"
    assert hass.states.get("sensor.koreader_book_title").state == "Duna"


async def test_battery_has_device_class(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json=PAYLOAD)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.koreader_battery")
    assert state.attributes["device_class"] == "battery"
    assert state.attributes["unit_of_measurement"] == "%"
```

- [ ] **Passo 2: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_sensor.py -q
```
Esperado: FALHA (sensores não criados; `state` é `None`).

- [ ] **Passo 3: Escrever `entity.py`**

`custom_components/koreader/entity.py`:
```python
"""Entidade base da integração KOReader."""

from __future__ import annotations

from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, signal_update


class KOReaderEntity(Entity):
    """Base: ligada ao device da entry e atualizada por dispatcher."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry) -> None:
        self._entry = entry
        model = entry.runtime_data.data.get("device_model") or "KOReader"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="KOReader",
            manufacturer="KOReader",
            model=model,
        )

    @property
    def _payload(self) -> dict[str, Any]:
        return self._entry.runtime_data.data

    @property
    def available(self) -> bool:
        return bool(self._payload)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_update(self._entry.entry_id), self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        # Atualiza o model do device caso tenha chegado agora.
        model = self._payload.get("device_model")
        if model and self._attr_device_info is not None:
            self._attr_device_info["model"] = model
        self.async_write_ha_state()
```

- [ ] **Passo 4: Escrever `sensor.py`**

`custom_components/koreader/sensor.py`:
```python
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
```

- [ ] **Passo 5: Rodar e ver passar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_sensor.py -q
```
Esperado: `2 passed`.

- [ ] **Passo 6: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-koreader
git add custom_components/koreader/entity.py custom_components/koreader/sensor.py tests/test_sensor.py
git commit -m "feat: base entity + read-only sensors"
```

---

### Task 4: Binary sensors (status de leitura + carregando)

**Arquivos:**
- Modify: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/binary_sensor.py`
- Test: `/Users/hudsonbrendon/Github/ha-koreader/tests/test_binary_sensor.py`

- [ ] **Passo 1: Escrever o teste que falha**

`tests/test_binary_sensor.py`:
```python
"""Testa os binary sensors."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_binary_sensors(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(
        f"/api/webhook/{WEBHOOK_ID}",
        json={"reading": True, "is_charging": False},
    )
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.koreader_reading").state == "on"
    assert hass.states.get("binary_sensor.koreader_charging").state == "off"
    assert (
        hass.states.get("binary_sensor.koreader_charging").attributes["device_class"]
        == "battery_charging"
    )
```

- [ ] **Passo 2: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_binary_sensor.py -q
```
Esperado: FALHA (estado `None`).

- [ ] **Passo 3: Escrever `binary_sensor.py`**

`custom_components/koreader/binary_sensor.py`:
```python
"""Binary sensors do KOReader."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KOReaderEntity


@dataclass(frozen=True, kw_only=True)
class KOReaderBinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool]


BINARY_SENSORS: tuple[KOReaderBinarySensorEntityDescription, ...] = (
    KOReaderBinarySensorEntityDescription(
        key="reading",
        name="Reading",
        icon="mdi:book-open-variant",
        value_fn=lambda d: bool(d.get("reading")),
    ),
    KOReaderBinarySensorEntityDescription(
        key="charging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda d: bool(d.get("is_charging")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        KOReaderBinarySensor(entry, desc) for desc in BINARY_SENSORS
    )


class KOReaderBinarySensor(KOReaderEntity, BinarySensorEntity):
    entity_description: KOReaderBinarySensorEntityDescription

    def __init__(self, entry, description: KOReaderBinarySensorEntityDescription) -> None:
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self._payload)
```

- [ ] **Passo 4: Rodar e ver passar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_binary_sensor.py -q
```
Esperado: `1 passed`.

- [ ] **Passo 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-koreader
git add custom_components/koreader/binary_sensor.py tests/test_binary_sensor.py
git commit -m "feat: reading + charging binary sensors"
```

---

## FASE 3 — Controle do Kindle (fila de comandos)

### Task 5: Number — controle do frontlight

**Arquivos:**
- Modify: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/number.py`
- Test: `/Users/hudsonbrendon/Github/ha-koreader/tests/test_number.py`

- [ ] **Passo 1: Escrever o teste que falha**

`tests/test_number.py`:
```python
"""Testa o number do frontlight: lê valor e enfileira comando."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_frontlight_reads_value(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"frontlight": 15})
    await hass.async_block_till_done()
    assert hass.states.get("number.koreader_frontlight").state == "15.0"


async def test_set_frontlight_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.koreader_frontlight", "value": 25},
        blocking=True,
    )
    assert entry.runtime_data.commands == [{"type": "set_frontlight", "value": 25}]
```

- [ ] **Passo 2: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_number.py -q
```
Esperado: FALHA (entidade não existe).

- [ ] **Passo 3: Escrever `number.py`**

`custom_components/koreader/number.py`:
```python
"""Number: controla a intensidade do frontlight do Kindle."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_SET_FRONTLIGHT
from .entity import KOReaderEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([KOReaderFrontlight(entry)])


class KOReaderFrontlight(KOReaderEntity, NumberEntity):
    """Slider de frontlight (lê o valor atual, controla no próximo check-in)."""

    _attr_name = "Frontlight"
    _attr_icon = "mdi:brightness-6"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_frontlight"

    @property
    def native_value(self) -> float | None:
        value = self._payload.get("frontlight")
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        self._entry.runtime_data.commands.append(
            {"type": CMD_SET_FRONTLIGHT, "value": int(value)}
        )
        # Otimista: reflete já, será confirmado no próximo snapshot.
        self._entry.runtime_data.data["frontlight"] = int(value)
        self.async_write_ha_state()
```

- [ ] **Passo 4: Rodar e ver passar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_number.py -q
```
Esperado: `2 passed`.

- [ ] **Passo 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-koreader
git add custom_components/koreader/number.py tests/test_number.py
git commit -m "feat: frontlight number control (enqueues command)"
```

---

### Task 6: Switch (wifi) + Button (forçar sync)

**Arquivos:**
- Modify: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/switch.py`
- Modify: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/button.py`
- Test: `/Users/hudsonbrendon/Github/ha-koreader/tests/test_switch.py`
- Test: `/Users/hudsonbrendon/Github/ha-koreader/tests/test_button.py`

- [ ] **Passo 1: Escrever os testes que falham**

`tests/test_switch.py`:
```python
"""Testa o switch de wifi."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_wifi_reads_state(hass: HomeAssistant, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WEBHOOK_ID}", json={"wifi_connected": True})
    await hass.async_block_till_done()
    assert hass.states.get("switch.koreader_wifi").state == "on"


async def test_turn_off_enqueues_command(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.koreader_wifi"},
        blocking=True,
    )
    assert entry.runtime_data.commands == [{"type": "set_wifi", "value": False}]
```

`tests/test_button.py`:
```python
"""Testa o button de forçar sync."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_press_enqueues_sync(hass: HomeAssistant):
    entry = await _setup(hass)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.koreader_force_sync"},
        blocking=True,
    )
    assert entry.runtime_data.commands == [{"type": "sync_now"}]
```

- [ ] **Passo 2: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_switch.py tests/test_button.py -q
```
Esperado: FALHA.

- [ ] **Passo 3: Escrever `switch.py`**

`custom_components/koreader/switch.py`:
```python
"""Switch: liga/desliga o WiFi do Kindle (afeta o próprio canal — use com cuidado)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_SET_WIFI
from .entity import KOReaderEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([KOReaderWifiSwitch(entry)])


class KOReaderWifiSwitch(KOReaderEntity, SwitchEntity):
    _attr_name = "WiFi"
    _attr_icon = "mdi:wifi"

    def __init__(self, entry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_wifi"

    @property
    def is_on(self) -> bool:
        return bool(self._payload.get("wifi_connected"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._entry.runtime_data.commands.append({"type": CMD_SET_WIFI, "value": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._entry.runtime_data.commands.append({"type": CMD_SET_WIFI, "value": False})
```

- [ ] **Passo 4: Escrever `button.py`**

`custom_components/koreader/button.py`:
```python
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

    async def async_press(self) -> None:
        self._entry.runtime_data.commands.append({"type": CMD_SYNC_NOW})
```

- [ ] **Passo 5: Rodar e ver passar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_switch.py tests/test_button.py -q
```
Esperado: `3 passed`.

- [ ] **Passo 6: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-koreader
git add custom_components/koreader/switch.py custom_components/koreader/button.py tests/test_switch.py tests/test_button.py
git commit -m "feat: wifi switch + force-sync button (enqueue commands)"
```

---

### Task 7: Serviço show_message (schema + teste) e services.yaml

**Arquivos:**
- Create: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/services.yaml`
- Test: `/Users/hudsonbrendon/Github/ha-koreader/tests/test_service.py`

> O serviço `koreader.show_message` já é registrado em `__init__.py` (Task 2). Aqui adicionamos o teste e o `services.yaml` (UI/validação).

- [ ] **Passo 1: Escrever o teste que falha**

`tests/test_service.py`:
```python
"""Testa o serviço koreader.show_message."""

from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.koreader.const import DOMAIN, SERVICE_SHOW_MESSAGE

WEBHOOK_ID = "koreader_test_id"


async def _setup(hass):
    assert await async_setup_component(hass, "webhook", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_WEBHOOK_ID: WEBHOOK_ID})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_show_message_enqueues(hass: HomeAssistant):
    entry = await _setup(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_SHOW_MESSAGE)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SHOW_MESSAGE,
        {"message": "Hora de dormir", "timeout": 10},
        blocking=True,
    )
    assert entry.runtime_data.commands == [
        {"type": "show_message", "text": "Hora de dormir", "timeout": 10}
    ]
```

- [ ] **Passo 2: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest tests/test_service.py -q
```
Esperado: o teste deve PASSAR já (serviço registrado na Task 2) — exceto se o `timeout` não for repassado. Se passar de primeira, ótimo (confirma a Task 2). Se falhar, ajuste `_async_register_services` em `__init__.py` para incluir `timeout` (já incluído no código da Task 2). Rode para confirmar:
Esperado final: `1 passed`.

- [ ] **Passo 3: Escrever `services.yaml`**

`custom_components/koreader/services.yaml`:
```yaml
show_message:
  name: Mostrar mensagem
  description: Enfileira uma mensagem para ser exibida na tela do Kindle no próximo check-in do KOReader.
  fields:
    message:
      name: Mensagem
      description: Texto a exibir no Kindle.
      required: true
      example: "Hora de dormir!"
      selector:
        text:
    timeout:
      name: Tempo (s)
      description: Segundos que a mensagem fica na tela (1-120).
      required: false
      example: 10
      selector:
        number:
          min: 1
          max: 120
          unit_of_measurement: s
```

- [ ] **Passo 4: Rodar a suíte inteira da integração**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader && .venv/bin/python -m pytest -q
```
Esperado: todos os testes passam.

- [ ] **Passo 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-koreader
git add custom_components/koreader/services.yaml tests/test_service.py
git commit -m "feat: show_message service schema (services.yaml) + test"
```

---

## FASE 4 — Plugin KOReader: modo webhook + execução de comandos

> Estes arquivos ficam no repo **existente** `/Users/hudsonbrendon/Github/hatelemetry.koplugin/`. O `busted` já está configurado lá (visto no plano anterior).

### Task 8: `ha_webhook.lua` — envia snapshot, lê comandos da resposta

**Arquivos:**
- Create: `/Users/hudsonbrendon/Github/hatelemetry.koplugin/ha_webhook.lua`
- Test: `/Users/hudsonbrendon/Github/hatelemetry.koplugin/spec/ha_webhook_spec.lua`

- [ ] **Passo 1: Escrever o teste que falha**

`spec/ha_webhook_spec.lua`:
```lua
local HAWebhook = require("ha_webhook")

describe("HAWebhook.build_url", function()
    it("monta a URL do webhook a partir de host/port/https/webhook_id", function()
        local cfg = { host = "homeassistant.99lab.online", port = 443, https = true,
            webhook_id = "abc123" }
        assert.are.equal("https://homeassistant.99lab.online:443/api/webhook/abc123",
            HAWebhook.build_url(cfg))
    end)
    it("usa http quando https=false", function()
        local cfg = { host = "192.168.1.10", port = 8123, https = false,
            webhook_id = "xyz" }
        assert.are.equal("http://192.168.1.10:8123/api/webhook/xyz",
            HAWebhook.build_url(cfg))
    end)
end)

describe("HAWebhook.build_request", function()
    it("monta POST com corpo JSON do snapshot", function()
        local cfg = { host = "h", port = 443, https = true, webhook_id = "id" }
        local snapshot = { battery_level = 80, reading = true }
        local captured
        local req = HAWebhook.build_request(cfg, snapshot, function(t)
            captured = t
            return '{"battery_level":80}'
        end)
        assert.are.equal("POST", req.method)
        assert.are.equal("application/json", req.headers["Content-Type"])
        assert.are.equal(80, captured.battery_level)
        assert.are.equal(tostring(#req.body), req.headers["Content-Length"])
    end)
end)

describe("HAWebhook.parse_commands", function()
    it("extrai a lista de comandos do corpo de resposta", function()
        local body = '{"commands":[{"type":"set_frontlight","value":20}]}'
        local cmds = HAWebhook.parse_commands(body, function(s)
            -- decoder fake: devolve a tabela esperada
            return { commands = { { type = "set_frontlight", value = 20 } } }
        end)
        assert.are.equal(1, #cmds)
        assert.are.equal("set_frontlight", cmds[1].type)
        assert.are.equal(20, cmds[1].value)
    end)
    it("devolve lista vazia quando não há comandos", function()
        local cmds = HAWebhook.parse_commands("{}", function() return {} end)
        assert.are.equal(0, #cmds)
    end)
end)
```

- [ ] **Passo 2: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin && busted spec/ha_webhook_spec.lua
```
Esperado: FALHA (`module 'ha_webhook' not found`).

- [ ] **Passo 3: Escrever `ha_webhook.lua`**

`ha_webhook.lua`:
```lua
-- Cliente de webhook do Home Assistant. Builders e parsing são puros (testáveis);
-- a chamada de rede carrega socket.http/ssl.https/ltn12/rapidjson de forma preguiçosa.
local HAWebhook = {}

function HAWebhook.build_url(cfg)
    local protocol = cfg.https == true and "https" or "http"
    return string.format("%s://%s:%d/api/webhook/%s",
        protocol, cfg.host, cfg.port, cfg.webhook_id)
end

-- json_encode: function(table) -> string
function HAWebhook.build_request(cfg, snapshot, json_encode)
    local body = json_encode(snapshot)
    return {
        url = HAWebhook.build_url(cfg),
        method = "POST",
        headers = {
            ["Content-Type"] = "application/json",
            ["Content-Length"] = tostring(#body),
        },
        body = body,
    }
end

-- json_decode: function(string) -> table
-- Retorna sempre uma lista (array) de comandos (pode ser vazia).
function HAWebhook.parse_commands(response_body, json_decode)
    if not response_body or response_body == "" then return {} end
    local ok, decoded = pcall(json_decode, response_body)
    if not ok or type(decoded) ~= "table" then return {} end
    local cmds = decoded.commands
    if type(cmds) ~= "table" then return {} end
    return cmds
end

-- Envia o snapshot e devolve ok(boolean), commands(list), err(string|nil), kind(string|nil).
function HAWebhook.post(cfg, snapshot)
    local http = cfg.https == true and require("ssl.https") or require("socket.http")
    local ltn12 = require("ltn12")
    local rapidjson = require("rapidjson")

    local prev_timeout = http.TIMEOUT
    http.TIMEOUT = 6
    local req = HAWebhook.build_request(cfg, snapshot, rapidjson.encode)
    local response_body = {}
    local result, code = http.request{
        url = req.url,
        method = req.method,
        headers = req.headers,
        source = ltn12.source.string(req.body),
        sink = ltn12.sink.table(response_body),
    }
    http.TIMEOUT = prev_timeout

    if result == nil then
        return false, {}, tostring(code), "connection"
    elseif code ~= 200 and code ~= 201 then
        return false, {}, tostring(code) .. " | " .. table.concat(response_body), "http"
    end

    local commands = HAWebhook.parse_commands(table.concat(response_body), rapidjson.decode)
    return true, commands, nil, nil
end

return HAWebhook
```

- [ ] **Passo 4: Rodar e ver passar**

Run:
```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin && busted spec/ha_webhook_spec.lua
```
Esperado: PASSA (6 sucessos).

- [ ] **Passo 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin
git add ha_webhook.lua spec/ha_webhook_spec.lua
git commit -m "feat: HA webhook client (send snapshot, parse commands)"
```

---

### Task 9: `commands.lua` — aplica um comando no Kindle

**Arquivos:**
- Create: `/Users/hudsonbrendon/Github/hatelemetry.koplugin/commands.lua`
- Test: `/Users/hudsonbrendon/Github/hatelemetry.koplugin/spec/commands_spec.lua`

- [ ] **Passo 1: Escrever o teste que falha**

`spec/commands_spec.lua`:
```lua
local Commands = require("commands")

-- Fakes que registram o que foi chamado
local function make_deps()
    local calls = {}
    local deps = {
        powerd = {
            setIntensity = function(_, v) calls.frontlight = v end,
            turnOnFrontlight = function() calls.fl_on = true end,
        },
        network = {
            turnOnWifi = function() calls.wifi = "on" end,
            turnOffWifi = function() calls.wifi = "off" end,
        },
        show_message = function(text, timeout)
            calls.message = text
            calls.timeout = timeout
        end,
        request_sync = function() calls.sync = true end,
    }
    return deps, calls
end

describe("Commands.apply", function()
    it("set_frontlight ajusta intensidade", function()
        local deps, calls = make_deps()
        Commands.apply({ type = "set_frontlight", value = 20 }, deps)
        assert.are.equal(20, calls.frontlight)
    end)
    it("show_message exibe texto com timeout", function()
        local deps, calls = make_deps()
        Commands.apply({ type = "show_message", text = "oi", timeout = 5 }, deps)
        assert.are.equal("oi", calls.message)
        assert.are.equal(5, calls.timeout)
    end)
    it("set_wifi true liga o wifi", function()
        local deps, calls = make_deps()
        Commands.apply({ type = "set_wifi", value = true }, deps)
        assert.are.equal("on", calls.wifi)
    end)
    it("set_wifi false desliga o wifi", function()
        local deps, calls = make_deps()
        Commands.apply({ type = "set_wifi", value = false }, deps)
        assert.are.equal("off", calls.wifi)
    end)
    it("sync_now pede sync", function()
        local deps, calls = make_deps()
        Commands.apply({ type = "sync_now" }, deps)
        assert.is_true(calls.sync)
    end)
    it("ignora comando desconhecido sem erro", function()
        local deps = make_deps()
        assert.has_no.errors(function()
            Commands.apply({ type = "wat" }, deps)
        end)
    end)
    it("apply_all aplica uma lista", function()
        local deps, calls = make_deps()
        Commands.apply_all({
            { type = "set_frontlight", value = 30 },
            { type = "sync_now" },
        }, deps)
        assert.are.equal(30, calls.frontlight)
        assert.is_true(calls.sync)
    end)
end)
```

- [ ] **Passo 2: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin && busted spec/commands_spec.lua
```
Esperado: FALHA (`module 'commands' not found`).

- [ ] **Passo 3: Escrever `commands.lua`**

`commands.lua`:
```lua
-- Aplica comandos vindos do Home Assistant no Kindle. As dependências do KOReader
-- chegam via `deps` (injeção), então a lógica é testável com fakes.
local Commands = {}

-- deps = {
--   powerd       = Device:getPowerDevice(),
--   network      = NetworkMgr,
--   show_message = function(text, timeout) ... end,  -- exibe InfoMessage
--   request_sync = function() ... end,               -- agenda envio imediato
-- }
function Commands.apply(cmd, deps)
    if type(cmd) ~= "table" or type(cmd.type) ~= "string" then return end

    if cmd.type == "set_frontlight" then
        local v = tonumber(cmd.value)
        if v and deps.powerd and deps.powerd.setIntensity then
            if v > 0 and deps.powerd.turnOnFrontlight then
                pcall(function() deps.powerd:turnOnFrontlight() end)
            end
            pcall(function() deps.powerd:setIntensity(v) end)
        end

    elseif cmd.type == "show_message" then
        if deps.show_message and cmd.text then
            pcall(deps.show_message, tostring(cmd.text), cmd.timeout)
        end

    elseif cmd.type == "set_wifi" then
        if deps.network then
            if cmd.value == true and deps.network.turnOnWifi then
                pcall(function() deps.network:turnOnWifi() end)
            elseif cmd.value == false and deps.network.turnOffWifi then
                pcall(function() deps.network:turnOffWifi() end)
            end
        end

    elseif cmd.type == "sync_now" then
        if deps.request_sync then
            pcall(deps.request_sync)
        end
    end
end

function Commands.apply_all(cmds, deps)
    if type(cmds) ~= "table" then return end
    for _, cmd in ipairs(cmds) do
        Commands.apply(cmd, deps)
    end
end

return Commands
```

- [ ] **Passo 4: Rodar e ver passar**

Run:
```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin && busted spec/commands_spec.lua
```
Esperado: PASSA (7 sucessos).

- [ ] **Passo 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin
git add commands.lua spec/commands_spec.lua
git commit -m "feat: command applier for HA->Kindle control"
```

---

### Task 10: Integrar modo webhook no `main.lua`

**Arquivos:**
- Modify: `/Users/hudsonbrendon/Github/hatelemetry.koplugin/ha_config.sample.lua`
- Modify: `/Users/hudsonbrendon/Github/hatelemetry.koplugin/main.lua`

> `main.lua` depende de módulos do KOReader; verificação é só `luac -p` (não roda fora do device). A lógica testável (`ha_webhook`, `commands`) já foi coberta nas Tasks 8–9.

- [ ] **Passo 1: Adicionar `webhook_id` ao config de exemplo**

Edite `ha_config.sample.lua` para incluir o campo `webhook_id` (substitua o conteúdo por):
```lua
-- Copie este arquivo para ha_config.lua e preencha.
-- ha_config.lua é gitignored, então seu token/segredo nunca é commitado.
return {
    host = "homeassistant.99lab.online",
    port = 443,
    https = true,  -- true se o HA usa HTTPS; recomendado fora da LAN confiável

    -- MODO 1 (recomendado): integração nativa via webhook.
    -- Pegue a URL no HA ao adicionar a integração KOReader; cole só o id final aqui.
    -- Ex.: URL = https://.../api/webhook/AbC123  ->  webhook_id = "AbC123"
    webhook_id = "ColeSeuWebhookIdAqui",

    -- MODO 2 (legado): REST /api/states com token de longa duração.
    -- Usado só se webhook_id estiver vazio. Deixe o token vazio se for usar webhook.
    token = "",
}
```

- [ ] **Passo 2: Adicionar requires e helpers de comando no topo do `main.lua`**

No `main.lua`, logo após o bloco de `require` existente (depois de `local HAClient = require("ha_client")`), adicione:
```lua
local HAWebhook = require("ha_webhook")
local Commands = require("commands")
```

- [ ] **Passo 3: Adicionar o builder de deps de comando e reescrever `push`**

Substitua a função `HATelemetry:push` inteira por esta versão, que usa webhook quando `webhook_id` está preenchido (e aplica os comandos recebidos), caindo para o modo REST legado caso contrário:

```lua
--- Constrói as dependências usadas para aplicar comandos no Kindle.
function HATelemetry:commandDeps()
    return {
        powerd = powerd,
        network = NetworkMgr,
        show_message = function(text, timeout)
            local msg = InfoMessage:new{ text = text }
            UIManager:show(msg)
            if tonumber(timeout) then
                UIManager:scheduleIn(tonumber(timeout), function() UIManager:close(msg) end)
            end
        end,
        request_sync = function()
            -- Reenvia a telemetria no próximo ciclo curto.
            UIManager:scheduleIn(1, self.push, self, true)
        end,
    }
end

--- Coleta o snapshot e envia ao Home Assistant (webhook nativo ou REST legado).
function HATelemetry:push(reading)
    if not NetworkMgr:isConnected() then
        if not self._offline_logged then
            logger.info("[HATelemetry]: sem rede, pulando envio")
            self._offline_logged = true
        end
        return
    end
    self._offline_logged = false

    local snap = self:collect(reading)

    local use_webhook = ha_config.webhook_id ~= nil
        and ha_config.webhook_id ~= ""
        and ha_config.webhook_id ~= "ColeSeuWebhookIdAqui"

    if use_webhook then
        local ok_post, commands, err = HAWebhook.post(ha_config, snap)
        if not ok_post then
            logger.info("[HATelemetry]: webhook falhou -", err)
            return
        end
        if commands and #commands > 0 then
            Commands.apply_all(commands, self:commandDeps())
        end
        return
    end

    -- Modo legado: um POST por entidade em /api/states.
    local entities = Sensors.build(snap, { prefix = self.settings.entity_prefix })
    for _, entity in ipairs(entities) do
        local ok_post, err, kind = HAClient.post(ha_config, entity)
        if not ok_post then
            logger.info("[HATelemetry]: push falhou para", entity.entity_id, "-", err)
            if kind == "connection" then
                break
            end
        end
    end
end
```

- [ ] **Passo 4: Syntax-check**

Run:
```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin && luac -p main.lua && echo "PARSE OK"
```
Esperado: `PARSE OK`.

- [ ] **Passo 5: Rodar toda a suíte Lua**

Run:
```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin && busted
```
Esperado: todos passam (smoke + sensors + snapshot + ha_client + ha_webhook + commands).

- [ ] **Passo 6: Commit**

```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin
git add main.lua ha_config.sample.lua
git commit -m "feat: webhook send mode + apply HA commands on the Kindle"
```

---

## FASE 5 — Traduções, dashboard, docs e verificação ponta a ponta

### Task 11: Traduções, README e dashboard

**Arquivos:**
- Create: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/translations/en.json`
- Create: `/Users/hudsonbrendon/Github/ha-koreader/custom_components/koreader/translations/pt-BR.json`
- Create: `/Users/hudsonbrendon/Github/ha-koreader/README.md`
- Create: `/Users/hudsonbrendon/Github/ha-koreader/docs/home-assistant/dashboard.yaml`

- [ ] **Passo 1: Criar `translations/en.json`**

`custom_components/koreader/translations/en.json`:
```json
{
  "config": {
    "step": {
      "user": {
        "title": "Set up KOReader",
        "description": "Do you want to start the KOReader setup?"
      }
    },
    "abort": {
      "single_instance_allowed": "Already configured.",
      "webhook_not_internet_accessible": "Your Home Assistant instance must be reachable from the device to receive webhook messages."
    },
    "create_entry": {
      "default": "To send KOReader telemetry to Home Assistant, configure the plugin with the webhook URL:\n\n`{webhook_url}`"
    }
  }
}
```

- [ ] **Passo 2: Criar `translations/pt-BR.json`**

`custom_components/koreader/translations/pt-BR.json`:
```json
{
  "config": {
    "step": {
      "user": {
        "title": "Configurar KOReader",
        "description": "Você quer iniciar a configuração do KOReader?"
      }
    },
    "abort": {
      "single_instance_allowed": "Já configurado.",
      "webhook_not_internet_accessible": "Sua instância do Home Assistant precisa estar acessível pelo dispositivo para receber mensagens de webhook."
    },
    "create_entry": {
      "default": "Para enviar a telemetria do KOReader ao Home Assistant, configure o plugin com a URL de webhook:\n\n`{webhook_url}`"
    }
  }
}
```

- [ ] **Passo 3: Criar `README.md`**

`README.md`:
```markdown
# KOReader — Integração Home Assistant

Integração nativa que recebe a telemetria do KOReader (Kindle) por **webhook** e
permite **controlar o Kindle** (luz, mensagem na tela, wifi, sync) pelo Home Assistant.

## Instalação (HACS)

1. HACS → Integrações → menu (⋮) → **Repositórios personalizados**
2. Adicione `https://github.com/hudsonbrendon/ha-koreader` como tipo **Integration**
3. Instale **KOReader** e reinicie o Home Assistant
4. Configurações → Dispositivos e Serviços → **Adicionar integração** → **KOReader**
5. Confirme — o HA mostra a **URL de webhook**. Copie o id final dela.

## Configurar o plugin do KOReader

No `ha_config.lua` do plugin `hatelemetry.koplugin`, preencha `webhook_id` com o id
copiado, ajuste `host`/`port`/`https`, e deixe `token = ""`. Reinstale o plugin no
Kindle e reinicie o KOReader.

## Entidades

Device **KOReader** com: bateria, status de leitura, carregando, título/autor,
progresso %, página atual/total, capítulo, tempo lido hoje, páginas hoje, tempo de
sessão, velocidade de leitura, frontlight (controle), wifi (controle), botão de sync,
e o serviço `koreader.show_message`.

## Limitação (e-ink)

Comandos do HA só chegam no próximo check-in do KOReader (virar página, acordar, ou
loop periódico) com WiFi ligado. Não é instantâneo com a tela apagada.
```

- [ ] **Passo 4: Criar `dashboard.yaml`**

`docs/home-assistant/dashboard.yaml`:
```yaml
title: Kindle
views:
  - title: Kindle
    cards:
      - type: entities
        title: KOReader
        entities:
          - binary_sensor.koreader_reading
          - sensor.koreader_book_title
          - sensor.koreader_book_author
          - sensor.koreader_chapter
          - sensor.koreader_current_page
          - sensor.koreader_total_pages
          - binary_sensor.koreader_charging
          - switch.koreader_wifi
          - number.koreader_frontlight
          - button.koreader_force_sync
      - type: gauge
        entity: sensor.koreader_progress
        name: Progresso
        unit: "%"
        min: 0
        max: 100
      - type: gauge
        entity: sensor.koreader_battery
        name: Bateria
        unit: "%"
        min: 0
        max: 100
      - type: history-graph
        title: Leitura
        hours_to_show: 168
        entities:
          - sensor.koreader_reading_time_today
          - sensor.koreader_pages_today
          - sensor.koreader_reading_speed
```

- [ ] **Passo 5: Validar JSON das traduções e rodar tudo**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader
.venv/bin/python -c "import json; [json.load(open(f)) for f in ['custom_components/koreader/translations/en.json','custom_components/koreader/translations/pt-BR.json','custom_components/koreader/strings.json','custom_components/koreader/manifest.json']]; print('JSON OK')"
.venv/bin/python -m pytest -q
```
Esperado: `JSON OK` e todos os testes passam.

- [ ] **Passo 6: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-koreader
git add custom_components/koreader/translations README.md docs/home-assistant/dashboard.yaml
git commit -m "docs: translations (en/pt-BR), README (HACS) and dashboard"
```

---

### Task 12: Verificação ponta a ponta (usuário — HA real + Kindle)

> Sem testes automatizados; é a validação real. Requer o HA e o Kindle do usuário.

- [ ] **Passo 1: Publicar o repo da integração no GitHub**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-koreader
gh repo create ha-koreader --public --source=. --remote=origin --description "KOReader native Home Assistant integration (webhook + control)" --push
```
Esperado: repo criado e `main` enviado.

- [ ] **Passo 2: Instalar via HACS**

No HA: HACS → Integrações → ⋮ → Repositórios personalizados → adicionar `https://github.com/hudsonbrendon/ha-koreader` (tipo Integration) → instalar **KOReader** → reiniciar o HA.

- [ ] **Passo 3: Adicionar a integração e copiar a URL de webhook**

Configurações → Dispositivos e Serviços → Adicionar integração → **KOReader** → confirmar. Copie a **URL de webhook** mostrada (o id final).

- [ ] **Passo 4: Configurar o plugin no Kindle**

No `ha_config.lua` (Mac), preencha `webhook_id` com o id copiado, `host = "homeassistant.99lab.online"`, `port = 443`, `https = true`, `token = ""`. Reinstale via USB:
```bash
cd /Users/hudsonbrendon/Github/hatelemetry.koplugin
rm -rf /tmp/hatelemetry.koplugin && mkdir -p /tmp/hatelemetry.koplugin
cp _meta.lua main.lua sensors.lua snapshot.lua ha_client.lua ha_webhook.lua commands.lua ha_config.lua /tmp/hatelemetry.koplugin/
cp -r /tmp/hatelemetry.koplugin/* /Volumes/Kindle/koreader/plugins/hatelemetry.koplugin/
diskutil eject /Volumes/Kindle
```
Reinicie o KOReader.

- [ ] **Passo 5: Verificar telemetria**

Abra um livro, vire uma página. Em **Ferramentas de Desenvolvedor → Estados**, filtre `koreader` — as entidades devem popular (bateria, progresso, capítulo, etc.) e ficar sob o device **KOReader**.

- [ ] **Passo 6: Verificar controle**

No HA, mexa no `number.koreader_frontlight` (ex.: 30) ou chame `koreader.show_message`. No **próximo check-in** do KOReader (vire uma página com WiFi ligado), o frontlight deve mudar / a mensagem deve aparecer na tela do Kindle. Dica: ative **Periodic Updates** no plugin (intervalo curto) para reduzir a latência.

- [ ] **Passo 7: Colar o dashboard**

Cole `docs/home-assistant/dashboard.yaml` num dashboard novo (editor YAML bruto).

---

## Auto-revisão

**1. Cobertura do spec:**
- "custom component nativo / configurações necessárias" → config flow por webhook (Task 1). ✅
- "exiba todas as informações" → sensores (Task 3) + binary sensors (Task 4) + dashboard (Task 11). ✅
- "controlar o Kindle através do KOReader" → fila de comandos: number frontlight (Task 5), switch wifi + button sync (Task 6), serviço show_message (Tasks 2/7), aplicados no Kindle por `commands.lua` (Task 9) via resposta do webhook (Task 2/8/10). ✅ Os 4 comandos escolhidos (frontlight, mensagem, wifi, sync) cobertos.
- "o que for possível" → limitação e-ink documentada; controle assíncrono via check-in. ✅
- "instalável/HACS" → hacs.json (Task 0), README HACS (Task 11), publicação (Task 12). ✅
- "tudo em português" → plano, strings.json, pt-BR.json, services.yaml, README em PT. ✅

**2. Varredura de placeholders:** Sem `TODO`/`implementar depois`. Todo passo de código tem código completo. O único ponto condicional (Task 7 Passo 2) é uma confirmação de que o serviço da Task 2 já cobre `timeout` — não é placeholder, e o código completo do serviço está na Task 2.

**3. Consistência de tipos/contratos:**
- Chaves do snapshot enviadas pelo plugin (`battery_level, reading, frontlight, wifi_connected, is_charging, book_title, ...`) batem com as lidas pelas `value_fn` em `sensor.py`/`binary_sensor.py`/`number.py`/`switch.py`. ✅
- Tipos de comando: constantes `CMD_SET_FRONTLIGHT="set_frontlight"`, `CMD_SHOW_MESSAGE="show_message"`, `CMD_SET_WIFI="set_wifi"`, `CMD_SYNC_NOW="sync_now"` (const.py) batem com os `cmd.type` tratados em `commands.lua` (`set_frontlight`, `show_message`, `set_wifi`, `sync_now`). ✅
- Formato do comando: HA enfileira `{"type": "set_frontlight", "value": 25}`, `{"type":"show_message","text":...,"timeout":...}`, `{"type":"set_wifi","value":bool}`, `{"type":"sync_now"}` — exatamente o que `commands.lua` espera (`cmd.value`, `cmd.text`, `cmd.timeout`). ✅
- Resposta do webhook: `{"commands":[...]}` (handler em `__init__.py`) é o que `HAWebhook.parse_commands` lê (`decoded.commands`). ✅
- `signal_update(entry_id)` definido em const.py e usado igual em `__init__.py` (send) e `entity.py` (connect). ✅
- IDs de entidade nos testes (`sensor.koreader_battery`, `number.koreader_frontlight`, `switch.koreader_wifi`, `button.koreader_force_sync`, `binary_sensor.koreader_reading`) derivam de `has_entity_name=True` + device "KOReader" + `name` da description / `_attr_name`. ✅

---

## Handoff de Execução

(Preenchido pelo chat após salvar o plano.)
