## Context

O sistema AIOps coleta eventos Kubernetes, analisa causa raiz via agente LangChain e persiste relatórios no PostgreSQL (PRD 002 — implementado). Falta a camada de entrega da informação ao usuário: interface web para visualização e notificação Discord para alertas proativos.

Estado atual relevante:
- **Report model** já existe com campos `id`, `markdown`, `status`, `event_uids`, `created_at`, `updated_at`
- **Status possíveis**: `EM_ANALISE`, `COMPLETO`, `INCOMPLETO`, `CORRIGINDO`, `CORRIGIDO`, `FALHA_CORRECAO`
- **Web router** existe com Jinja2 (`GET /` apenas)
- **base.html** completo com dark theme, badges de status e estilos de botão
- **Dependências** `markdown` e `httpx` já estão no `pyproject.toml`
- **EventHandler._run_analysis** é o ponto onde o relatório é finalizado (status → COMPLETO/INCOMPLETO)

## Goals / Non-Goals

**Goals:**
- Interface web funcional para listagem e detalhe de relatórios, servida pela própria API FastAPI com Jinja2
- Notificação automática no Discord após geração de relatório, sem bloquear o fluxo principal
- Configuração simples via variáveis de ambiente

**Non-Goals:**
- Autenticação e autorização
- Paginação, filtros ou busca na listagem
- Dashboard com métricas agregadas
- Lógica de correção (PRD 004)
- Notificação de resultado de correção

## Decisions

### 1. Rotas web no router existente (`web/router.py`)

As novas rotas `GET /reports` e `GET /reports/{id}` serão adicionadas ao `web/router.py` existente. A sessão do banco será obtida via dependência FastAPI injetando o `async_sessionmaker` configurado no `main.py` via `app.state`.

**Alternativa descartada:** Criar um router separado para reports — desnecessário dado o tamanho do módulo.

### 2. Renderização Markdown com biblioteca `markdown`

Usar a biblioteca `markdown` (já no `pyproject.toml`) com extensão `tables` e `fenced_code` para converter o conteúdo do relatório em HTML. A conversão acontece no momento da renderização do template (na rota, antes de passar ao Jinja2), não no template em si.

**Alternativa descartada:** `markdown-it-py` — mais pesada, sem benefício para o caso de uso.

### 3. Notificação Discord via `httpx` (HTTP direto)

Usar `httpx.AsyncClient` para enviar mensagens via Discord REST API (`POST /channels/{channel_id}/messages`). Não usar biblioteca `discord.py` — seria overkill para enviar mensagens simples.

**Alternativa descartada:** `discord.py` — requer gateway WebSocket, é feito para bots interativos, não para notificações unidirecionais.

### 4. Módulo `notifications/discord.py` com função assíncrona

Criar um módulo dedicado com função `send_discord_notification(report_id, summary, base_url)` que encapsula a chamada HTTP com retry. O módulo valida configuração no momento do envio e loga `WARNING` se variáveis não estiverem configuradas.

### 5. Ponto de integração: final do `_run_analysis` no `EventHandler`

A notificação Discord será chamada ao final do método `_run_analysis` no `event_handler.py`, após a persistência bem-sucedida do relatório com status `COMPLETO`. Relatórios `INCOMPLETO` não geram notificação.

**Alternativa descartada:** Usar evento/signal do SQLAlchemy — complexidade desnecessária para um único ponto de integração.

### 6. Botão "Executar correção" como placeholder

O botão será renderizado na página de detalhe para relatórios com status `COMPLETO`, mas desabilitado com alerta visual informando que a funcionalidade será implementada no PRD 004. Não haverá endpoint stub.

### 7. Retry com backoff exponencial (3 tentativas)

A função de envio Discord implementa retry com backoff exponencial: 1s → 2s → 4s, máximo 3 tentativas. Após esgotar, loga o erro e retorna silenciosamente. O fluxo principal nunca é bloqueado.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Interface sem autenticação exposta | Restringir acesso via rede (VPN, ingress interno). Documentar limitação. |
| Discord API indisponível | Retry com backoff + fallback silencioso. Notificação é best-effort. |
| Token Discord invalidado pós-startup | Falhar silenciosamente a cada tentativa, logar erro. Não desabilita automaticamente. |
| Markdown malformado no relatório | Biblioteca `markdown` renderiza o que for possível sem quebrar a página. |
| `APP_BASE_URL` incorreta gera links quebrados | Valor padrão `http://localhost:8000` para dev. Documentar necessidade de configurar em produção. |
