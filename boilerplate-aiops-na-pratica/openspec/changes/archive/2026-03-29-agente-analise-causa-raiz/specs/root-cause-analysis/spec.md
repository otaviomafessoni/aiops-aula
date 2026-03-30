## ADDED Requirements

### Requirement: Agente ReAct com LangChain e Claude Sonnet
O sistema SHALL construir um agente usando `create_agent` de `langchain.agents` com `ChatAnthropic` (Claude Sonnet) e padrão ReAct. O agente SHALL se conectar ao cluster Kubernetes via `MultiServerMCPClient` (langchain-mcp-adapters) usando o MCP Server Kubernetes (Flux159) via transporte HTTP. O MCP Server SHALL rodar como container no docker-compose do projeto. A URL SHALL ser configurável via variável de ambiente `MCP_KUBERNETES_URL`.

#### Scenario: Agente investiga evento de CrashLoopBackOff
- **WHEN** o agente recebe eventos Warning de CrashLoopBackOff
- **THEN** o agente SHALL usar as tools MCP (kubectl_get, kubectl_describe, kubectl_logs) para investigar o estado dos recursos afetados e identificar a causa raiz

#### Scenario: Agente executa ciclo ReAct
- **WHEN** o agente inicia uma investigação
- **THEN** o agente SHALL iterar no ciclo análise → ação → reflexão → próxima ação até identificar a causa raiz ou atingir o limite de iterações

### Requirement: Limite de iterações configurável
O sistema SHALL limitar o número de chamadas de tools do agente via `ToolCallLimitMiddleware` com `run_limit` configurável pela variável de ambiente `AGENT_MAX_ITERATIONS` (padrão: 25). O `exit_behavior` SHALL ser `'continue'` — ao atingir o limite, o agente SHALL parar de chamar tools e gerar uma resposta final indicando que a investigação foi inconclusiva e que o problema deve ser investigado manualmente.

#### Scenario: Agente atinge limite de iterações
- **WHEN** o agente atinge o `run_limit` sem identificar causa raiz
- **THEN** o agente SHALL parar de chamar tools, gerar resposta indicando investigação inconclusiva e necessidade de análise manual, e o relatório SHALL ser salvo com status INCOMPLETO

#### Scenario: Variável AGENT_MAX_ITERATIONS com valor válido
- **WHEN** `AGENT_MAX_ITERATIONS` está definida como "15"
- **THEN** o `run_limit` do middleware SHALL ser configurado como 15

#### Scenario: Variável AGENT_MAX_ITERATIONS com valor inválido
- **WHEN** `AGENT_MAX_ITERATIONS` contém valor não-numérico, negativo ou zero
- **THEN** o sistema SHALL usar o padrão de 25 e registrar warning no log

### Requirement: Prompt estruturado de investigação
O agente SHALL receber um system_prompt que define: papel de analista Kubernetes, regras de investigação (apenas diagnóstico, nunca executar patch/apply/delete), ferramentas disponíveis (kubectl_get, kubectl_describe, kubectl_logs), classificação de severidade (CRITICO, ALTO, MEDIO, BAIXO) e formato de resposta Markdown.

#### Scenario: Agente segue regras de investigação
- **WHEN** o agente investiga eventos
- **THEN** o agente SHALL usar apenas ferramentas de leitura (kubectl_get, kubectl_describe, kubectl_logs) e SHALL NOT executar kubectl_patch, kubectl_apply ou kubectl_delete

### Requirement: Execução em background
A análise do agente SHALL ser executada em background via `asyncio.create_task` para não bloquear o ciclo de coleta. O relatório SHALL ser criado com status EM_ANALISE antes de disparar a task em background.

#### Scenario: Coleta não bloqueia durante análise
- **WHEN** o agente está executando análise de um batch de eventos
- **THEN** o próximo ciclo de coleta SHALL executar normalmente sem aguardar a conclusão da análise

#### Scenario: Falha na task em background
- **WHEN** a task em background falha por erro inesperado
- **THEN** o relatório SHALL ser atualizado para status INCOMPLETO e o erro SHALL ser registrado no log

### Requirement: Resiliência a falhas do MCP e API
O sistema SHALL tratar indisponibilidade do MCP Server Kubernetes abortando a análise e atualizando o relatório para INCOMPLETO. Para erros da API do Claude (rate limit, timeout), SHALL aplicar retry com backoff exponencial até 3 tentativas antes de abortar.

#### Scenario: MCP Server Kubernetes indisponível
- **WHEN** o MCP Server Kubernetes não está acessível durante a análise
- **THEN** a análise SHALL ser abortada, o relatório SHALL ser atualizado para INCOMPLETO e o erro SHALL ser registrado no log

#### Scenario: Rate limit da API Claude
- **WHEN** a API do Claude retorna rate limit durante a análise
- **THEN** o sistema SHALL aplicar retry com backoff exponencial até 3 tentativas antes de abortar
