## Context

O sistema AIOps já possui um pipeline funcional: coleta de eventos K8s → análise de causa raiz via agente LangChain → relatório persistido no PostgreSQL → interface web + notificação Discord. O relatório inclui passos de correção recomendados, mas a execução é manual. O botão "Executar correção" já existe na interface (placeholder desabilitado).

O agente de análise (`root_cause_agent.py`) estabelece o padrão: prompt carregado de arquivo, `ChatAnthropic`, tools via `get_kubernetes_tools()`, `create_agent` com middleware de limite de iterações.

## Goals / Non-Goals

**Goals:**
- Agente de correção que executa passos do relatório no cluster via MCP
- Endpoint API assíncrono para acionar a correção
- Verificação pós-correção para validar se o problema foi resolvido
- Resultado da correção persistido e visível na interface
- Notificação Discord do resultado

**Non-Goals:**
- Whitelist de ações permitidas, dry-run, restrição por namespace
- Aprovação humana além do clique no botão
- Rollback automático
- Nova página para resultado da correção (exibido na mesma página de detalhe)

## Decisions

### 1. Agente separado em `fix_agent.py`
Mesmo padrão do `root_cause_agent.py`: prompt em arquivo, `ChatAnthropic`, tools MCP, `create_agent`. Dois agentes paralelos, sem abstração "base agent" — complexidade desnecessária para dois arquivos.

**Alternativa descartada:** Agente único que faz análise e correção. Motivo: responsabilidades distintas, evolução independente.

### 2. Campo `fix_result` na tabela `reports`
Novo campo `Text`, nullable, para persistir o resultado da correção (Markdown gerado pelo agente). Migration Alembic.

**Alternativa descartada:** Tabela separada `fix_executions`. Motivo: over-engineering para v1; um relatório tem no máximo uma correção.

### 3. Endpoint `POST /reports/{id}/fix` em `api/router.py`
Retorna `202 Accepted` e processa em background via `asyncio.create_task`. Validação simples de status (sem SELECT FOR UPDATE).

**Alternativa descartada:** Endpoint no `web/router.py`. Motivo: desacoplar da interface permite futuramente acionar por outras vias.

### 4. Verificação pós-correção com espera de 15 segundos
Hardcoded. Após executar os passos, aguarda 15s e então verifica estado dos recursos via MCP.

### 5. Reutilização de `send_discord_notification`
A função existente aceita `report_id`, `summary` e `base_url` — suficiente para notificar correção. O chamador formata o resumo adequado ao contexto.

### 6. Parsing da resposta do agente
Primeira linha determina o status: `CORRIGIDO:` → CORRIGIDO, `FALHA:` → FALHA_CORRECAO, formato inesperado → FALHA_CORRECAO com warning no log.

### 7. Retry com backoff para erros da API Claude
3 tentativas. Após esgotar, abortar com FALHA_CORRECAO. Mesmo padrão de resiliência do módulo Discord.

## Risks / Trade-offs

- **Acesso irrestrito ao cluster** → Risco aceito para contexto educacional. Documentar como melhoria futura.
- **Sem rollback automático** → Se correção piorar o estado, intervenção manual necessária. O relatório fica disponível para revisão.
- **Verificação pós-correção com tempo fixo (15s)** → Pode ser insuficiente para recursos que demoram mais para estabilizar. Aceito na v1.
- **Race condition teórica no status** → Verificação simples sem lock. Risco baixo no contexto educacional com poucos usuários simultâneos.
