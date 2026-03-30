## MODIFIED Requirements

### Requirement: Botão de correção placeholder
A página de detalhe SHALL exibir um botão "Executar correção" para relatórios com status `COMPLETO`. O botão SHALL estar habilitado e, ao ser clicado, SHALL fazer `POST /api/reports/{id}/fix` via JavaScript. Para relatórios com status `CORRIGINDO`, o botão SHALL estar desabilitado com texto "Correção em andamento...". Para status `CORRIGIDO` ou `FALHA_CORRECAO`, o botão não SHALL ser exibido.

#### Scenario: Relatório COMPLETO sem correção ativa
- **WHEN** o usuário visualiza um relatório com status `COMPLETO`
- **THEN** a página exibe botão "Executar correção" habilitado que ao clique faz POST para `/api/reports/{id}/fix`

#### Scenario: Relatório com correção em andamento
- **WHEN** o usuário visualiza um relatório com status `CORRIGINDO`
- **THEN** a página exibe botão desabilitado com texto "Correção em andamento..."

#### Scenario: Relatório em análise ou incompleto
- **WHEN** o usuário visualiza um relatório com status `EM_ANALISE` ou `INCOMPLETO`
- **THEN** a página não exibe o botão de correção

### Requirement: Exibição do resultado da correção
A página de detalhe SHALL exibir o resultado da correção (`fix_result`) quando disponível. O conteúdo Markdown SHALL ser convertido para HTML usando a mesma biblioteca e extensões da análise. O resultado SHALL ser exibido abaixo do relatório de análise, em seção separada com título "Resultado da Correção".

#### Scenario: Relatório com resultado de correção
- **WHEN** o usuário visualiza um relatório com status `CORRIGIDO` ou `FALHA_CORRECAO` e `fix_result` preenchido
- **THEN** a página exibe o relatório de análise e abaixo uma seção "Resultado da Correção" com o conteúdo renderizado em HTML

#### Scenario: Relatório sem resultado de correção
- **WHEN** o usuário visualiza um relatório com `fix_result` vazio/null
- **THEN** a seção "Resultado da Correção" não é exibida
