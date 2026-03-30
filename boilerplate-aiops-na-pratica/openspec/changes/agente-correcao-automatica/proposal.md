## Why

Os relatórios de análise (PRD 002) geram passos de correção recomendados, mas a execução é manual — o operador precisa ler, interpretar e executar comandos no cluster. Isso adiciona tempo ao MTTR e está sujeito a erros. Automatizar a correção fecha o loop do pipeline AIOps.

## What Changes

- Novo agente LangChain de correção que lê o relatório e executa os passos via MCP Server Kubernetes
- Novo endpoint `POST /reports/{id}/fix` em `api/router.py` que aciona a correção em background
- Novo campo `fix_result` (Text) na tabela `reports` para persistir o resultado da correção
- Verificação pós-correção (15s de espera + checagem via MCP) antes de declarar sucesso/falha
- Notificação Discord reutilizando `send_discord_notification` existente com resumo do resultado
- Novos status no fluxo do relatório: `CORRIGINDO`, `CORRIGIDO`, `FALHA_CORRECAO`
- Resultado da correção exibido na página de detalhe do relatório existente (sem página nova)

## Capabilities

### New Capabilities
- `auto-fix-agent`: Agente LangChain que executa correções no cluster Kubernetes via MCP a partir dos passos de um relatório de análise
- `fix-endpoint`: Endpoint API para acionar correção assíncrona com validação de status e proteção contra execução duplicada

### Modified Capabilities
- `report-persistence`: Novo campo `fix_result` e novos status (`CORRIGINDO`, `CORRIGIDO`, `FALHA_CORRECAO`)
- `report-web-interface`: Exibição do resultado da correção na página de detalhe do relatório
- `discord-notification`: Reutilização para notificar resultado da correção (sem mudança de interface, apenas chamada com dados diferentes)

## Impact

- **Código**: `agents/`, `api/router.py`, `models/report.py`, `web/router.py`, templates
- **Banco de dados**: Nova migration Alembic para campo `fix_result`
- **APIs**: Novo endpoint `POST /reports/{id}/fix`
- **Dependências**: Mesmas do agente de análise (LangChain, langchain-anthropic, MCP)
- **Risco documentado**: Agente com acesso irrestrito ao cluster na v1 (contexto educacional)
