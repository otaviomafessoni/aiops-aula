## Why

Os relatórios de análise de causa raiz (PRD 002) são gerados e persistidos no PostgreSQL, mas não há forma de visualizá-los nem de ser notificado quando um novo relatório é criado. O operador precisaria consultar o banco diretamente — anulando o benefício da automação. Sem interface de visualização e notificação proativa, a informação não chega a quem precisa agir.

## What Changes

- Criar página web de listagem de todos os relatórios de análise, ordenados por data (mais recente primeiro)
- Criar página web de detalhe do relatório com renderização Markdown → HTML
- Adicionar botão "Executar correção" na página de detalhe (desabilitado com alerta — PRD 004 ainda não implementado)
- Implementar bot Discord que envia notificação automática após geração de cada relatório
- A notificação contém ID do problema, resumo da causa raiz e link direto para o relatório na interface web
- Novas variáveis de ambiente: `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`, `APP_BASE_URL`

## Capabilities

### New Capabilities
- `report-web-interface`: Interface web server-side (Jinja2) para listagem e visualização detalhada de relatórios de análise de causa raiz
- `discord-notification`: Notificação automática via bot Discord após geração de relatório, com retry e fallback silencioso

### Modified Capabilities

Nenhuma capability existente tem requisitos alterados.

## Impact

- **Código**: Novos templates Jinja2 (listagem, detalhe), novas rotas no web router, novo módulo `notifications/discord.py`, integração no fluxo pós-análise do `event_handler.py`
- **Dependências**: `markdown` (renderização Markdown → HTML), `aiohttp` ou `httpx` (chamadas à Discord API)
- **APIs**: Novas rotas `GET /reports` e `GET /reports/{id}`, integração com Discord API
- **Infraestrutura**: Requer bot Discord configurado (token + canal) e `APP_BASE_URL` para links funcionais
