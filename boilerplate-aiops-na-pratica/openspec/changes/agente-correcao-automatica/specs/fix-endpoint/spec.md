## ADDED Requirements

### Requirement: Endpoint de acionamento de correção
O sistema SHALL expor um endpoint `POST /api/reports/{id}/fix` em `api/router.py`. O endpoint SHALL validar que o relatório existe e tem status COMPLETO, atualizar o status para CORRIGINDO, retornar `202 Accepted` e disparar a correção em background via `asyncio.create_task`.

#### Scenario: Acionamento com relatório COMPLETO
- **WHEN** `POST /api/reports/{id}/fix` é chamado com um relatório em status COMPLETO
- **THEN** o endpoint atualiza status para CORRIGINDO, retorna `202 Accepted` com corpo `{"status": "accepted", "message": "Correção iniciada"}` e dispara o agente em background

#### Scenario: Relatório com status diferente de COMPLETO
- **WHEN** `POST /api/reports/{id}/fix` é chamado com relatório em status EM_ANALISE, INCOMPLETO, CORRIGINDO, CORRIGIDO ou FALHA_CORRECAO
- **THEN** o endpoint retorna `409 Conflict` com mensagem explicativa

#### Scenario: Relatório não encontrado
- **WHEN** `POST /api/reports/{id}/fix` é chamado com ID inexistente
- **THEN** o endpoint retorna `404 Not Found`

#### Scenario: Proteção contra execução duplicada
- **WHEN** dois requests simultâneos chegam para o mesmo relatório COMPLETO
- **THEN** o primeiro atualiza para CORRIGINDO e o segundo recebe `409 Conflict` (verificação simples de status)

### Requirement: Processamento em background
A task background SHALL: executar o agente de correção, persistir o resultado em `fix_result`, atualizar o status (CORRIGIDO ou FALHA_CORRECAO) e enviar notificação Discord. Se o agente lançar exceção não tratada, o status SHALL ser atualizado para FALHA_CORRECAO.

#### Scenario: Correção bem-sucedida em background
- **WHEN** o agente conclui com sucesso
- **THEN** `fix_result` é preenchido, status é CORRIGIDO e notificação Discord é enviada

#### Scenario: Exceção não tratada durante correção
- **WHEN** ocorre uma exceção inesperada durante a execução do agente
- **THEN** status é atualizado para FALHA_CORRECAO, erro é logado e notificação Discord é enviada
