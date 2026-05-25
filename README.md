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
