## 1. Interface Web — Listagem de Relatórios

- [x] 1.1 Criar função de query para listar relatórios ordenados por `created_at` desc (models ou web router)
- [x] 1.2 Criar rota `GET /reports` no `web/router.py` com injeção de sessão via `app.state`
- [x] 1.3 Criar template Jinja2 `reports_list.html` com listagem (ID, data, badge de status, resumo clicável)
- [x] 1.4 Tratar cenário de lista vazia (mensagem "Nenhum relatório encontrado")
- [x] 1.5 Tratar cenário de erro de conexão com PostgreSQL (renderizar página de erro genérica)

## 2. Interface Web — Detalhe do Relatório

- [x] 2.1 Criar rota `GET /reports/{id}` no `web/router.py` com conversão Markdown → HTML via biblioteca `markdown`
- [x] 2.2 Criar template Jinja2 `report_detail.html` com conteúdo HTML renderizado, badge de status e data
- [x] 2.3 Adicionar botão "Executar correção" desabilitado com alerta para relatórios `COMPLETO`
- [x] 2.4 Adicionar botão desabilitado "Correção em andamento..." para relatórios `CORRIGINDO`
- [x] 2.5 Tratar cenário de relatório não encontrado (página 404)
- [x] 2.6 Adicionar estilos CSS para renderização do Markdown (headings, tabelas, code blocks) no `base.html` ou template

## 3. Navegação

- [x] 3.1 Atualizar link de navegação no `base.html` para apontar para `/reports`
- [x] 3.2 Redirecionar `GET /` para `/reports`

## 4. Notificação Discord

- [x] 4.1 Criar módulo `notifications/discord.py` com função `send_discord_notification(report_id, summary, base_url)`
- [x] 4.2 Implementar envio via `httpx.AsyncClient` para Discord REST API (`POST /channels/{channel_id}/messages`)
- [x] 4.3 Implementar retry com backoff exponencial (3 tentativas: 1s → 2s → 4s)
- [x] 4.4 Implementar validação de variáveis de ambiente (`DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`) com log `WARNING` a cada tentativa quando ausentes
- [x] 4.5 Formatar mensagem em texto simples com ID do relatório, resumo e link `{APP_BASE_URL}/reports/{id}`

## 5. Integração no Fluxo

- [x] 5.1 Chamar `send_discord_notification` ao final de `EventHandler._run_analysis` quando status for `COMPLETO`
- [x] 5.2 Garantir que falha na notificação não bloqueia nem altera o fluxo de análise existente
