## ADDED Requirements

### Requirement: Agente de correção automática
O sistema SHALL implementar um agente LangChain em `agents/fix_agent.py` que recebe o conteúdo Markdown de um relatório de análise e executa os passos de correção no cluster Kubernetes via MCP Server. O agente SHALL usar `ChatAnthropic` com modelo `claude-sonnet-4-20250514` e tools obtidas via `get_kubernetes_tools()`. O prompt SHALL ser carregado de `agents/prompts/fix.md`. O agente SHALL respeitar o limite de iterações configurado em `AGENT_MAX_ITERATIONS`.

#### Scenario: Correção bem-sucedida
- **WHEN** o agente recebe um relatório com passos de correção válidos e os recursos existem no cluster
- **THEN** o agente executa os passos via MCP, aguarda 15 segundos, verifica o estado e retorna resposta com primeira linha `CORRIGIDO: [resumo]`

#### Scenario: Correção com falha
- **WHEN** o agente executa os passos mas a verificação pós-correção indica que o problema persiste
- **THEN** o agente retorna resposta com primeira linha `FALHA: [resumo]`

#### Scenario: Recurso não encontrado
- **WHEN** um passo de correção referencia um recurso que não existe mais no cluster
- **THEN** o agente registra que o recurso não foi encontrado e continua com os próximos passos

### Requirement: Prompt do agente de correção
O prompt SHALL ser armazenado em `agents/prompts/fix.md` e SHALL instruir o agente a seguir o padrão ReAct (raciocinar → verificar estado → executar → validar). O prompt SHALL incluir regras de segurança: nunca deletar namespaces, PVCs ou recursos em kube-system; nunca escalar para 0 réplicas; nunca chamar mesma ferramenta com mesmos parâmetros duas vezes; abortar após 2 falhas na mesma ferramenta.

#### Scenario: Agente segue padrão ReAct
- **WHEN** o agente processa um passo de correção
- **THEN** o agente primeiro verifica o estado atual do recurso, depois executa a correção, depois valida o resultado

### Requirement: Parsing da resposta do agente
O sistema SHALL interpretar a primeira linha da resposta do agente para determinar o status final. Se começa com `CORRIGIDO:` → status CORRIGIDO. Se começa com `FALHA:` → status FALHA_CORRECAO. Se formato inesperado → status FALHA_CORRECAO com warning no log.

#### Scenario: Resposta com formato esperado CORRIGIDO
- **WHEN** a primeira linha da resposta do agente é `CORRIGIDO: pods reiniciados com sucesso`
- **THEN** o sistema define o status como CORRIGIDO

#### Scenario: Resposta com formato esperado FALHA
- **WHEN** a primeira linha da resposta do agente é `FALHA: recurso não encontrado`
- **THEN** o sistema define o status como FALHA_CORRECAO

#### Scenario: Resposta com formato inesperado
- **WHEN** a primeira linha da resposta do agente não começa com `CORRIGIDO:` nem `FALHA:`
- **THEN** o sistema define o status como FALHA_CORRECAO e loga warning

### Requirement: Verificação pós-correção
Após executar os passos de correção, o agente SHALL aguardar 15 segundos e então verificar o estado dos recursos no cluster via MCP para confirmar se o problema foi resolvido.

#### Scenario: Problema resolvido após espera
- **WHEN** o agente executa a correção e após 15 segundos os recursos estão no estado esperado
- **THEN** o agente reporta como CORRIGIDO

#### Scenario: Problema persiste após espera
- **WHEN** o agente executa a correção e após 15 segundos os recursos ainda estão em estado problemático
- **THEN** o agente reporta como FALHA

### Requirement: Retry com backoff para erros da API
O sistema SHALL implementar retry com backoff exponencial para erros da API Claude durante a execução do agente: 3 tentativas. Após esgotar, o sistema SHALL abortar e retornar FALHA_CORRECAO.

#### Scenario: API Claude temporariamente indisponível
- **WHEN** a API Claude falha na primeira tentativa mas funciona na segunda
- **THEN** o sistema retenta com backoff e completa a correção

#### Scenario: API Claude totalmente indisponível
- **WHEN** a API Claude falha em todas as 3 tentativas
- **THEN** o sistema aborta e define status como FALHA_CORRECAO
