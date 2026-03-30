## ADDED Requirements

### Requirement: Listagem de relatórios
O sistema SHALL exibir uma página web em `GET /reports` com todos os relatórios de análise ordenados por data de criação (mais recente primeiro). Cada item da lista SHALL exibir: ID, data de criação, status (com badge visual) e resumo (primeiras linhas da causa raiz). Cada item SHALL ser clicável e navegar para a página de detalhe. A página SHALL ser servida pela API FastAPI com template Jinja2.

#### Scenario: Listagem com relatórios existentes
- **WHEN** o usuário acessa `GET /reports` e existem relatórios no banco
- **THEN** a página exibe todos os relatórios ordenados por `created_at` decrescente, cada um com ID, data, badge de status e resumo clicável

#### Scenario: Listagem sem relatórios
- **WHEN** o usuário acessa `GET /reports` e não há relatórios no banco
- **THEN** a página exibe mensagem informativa "Nenhum relatório encontrado"

#### Scenario: Erro de conexão com PostgreSQL
- **WHEN** o usuário acessa `GET /reports` e o banco está indisponível
- **THEN** o sistema exibe página de erro genérica com mensagem amigável

### Requirement: Visualização detalhada do relatório
O sistema SHALL exibir uma página web em `GET /reports/{id}` com o conteúdo completo do relatório. O conteúdo Markdown SHALL ser convertido para HTML usando a biblioteca `markdown` com extensões `tables` e `fenced_code`. A página SHALL exibir o status atual do relatório com badge visual.

#### Scenario: Visualização de relatório existente
- **WHEN** o usuário acessa `GET /reports/{id}` com um ID válido
- **THEN** a página renderiza o Markdown completo do relatório em HTML, exibe o status atual com badge e a data de criação

#### Scenario: Relatório não encontrado
- **WHEN** o usuário acessa `GET /reports/{id}` com um ID inexistente
- **THEN** o sistema retorna página 404 com mensagem informativa

#### Scenario: Markdown malformado
- **WHEN** o relatório contém Markdown malformado
- **THEN** o sistema renderiza o que for possível sem quebrar a página

### Requirement: Botão de correção placeholder
A página de detalhe SHALL exibir um botão "Executar correção" para relatórios com status `COMPLETO`. O botão SHALL estar desabilitado com alerta visual informando que a funcionalidade será implementada futuramente (PRD 004). Para relatórios com status `CORRIGINDO`, o botão SHALL estar desabilitado com texto "Correção em andamento...".

#### Scenario: Relatório COMPLETO sem correção ativa
- **WHEN** o usuário visualiza um relatório com status `COMPLETO`
- **THEN** a página exibe botão "Executar correção" desabilitado com alerta informando que será implementado futuramente

#### Scenario: Relatório com correção em andamento
- **WHEN** o usuário visualiza um relatório com status `CORRIGINDO`
- **THEN** a página exibe botão desabilitado com texto "Correção em andamento..."

#### Scenario: Relatório em análise ou incompleto
- **WHEN** o usuário visualiza um relatório com status `EM_ANALISE` ou `INCOMPLETO`
- **THEN** a página não exibe o botão de correção
