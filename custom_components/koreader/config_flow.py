"""Config flow da integração KOReader (webhook)."""

from homeassistant.helpers import config_entry_flow

from .const import DOMAIN

config_entry_flow.register_webhook_flow(
    DOMAIN,
    "KOReader Webhook",
    {"docs_url": "https://github.com/hudsonbrendon/ha-koreader"},
    allow_multiple=True,
)
