## ADDED Requirements

### Requirement: Modelo de dados Report
O sistema SHALL criar uma tabela `reports` no PostgreSQL com os campos: `id` (UUID, PK), `markdown` (TEXT), `status` (VARCHAR), `event_uids` (TEXT[] com GIN index), `created_at` (TIMESTAMP WITH TIME ZONE) e `updated_at` (TIMESTAMP WITH TIME ZONE). A migration SHALL ser gerenciada via Alembic.

#### Scenario: Criação da tabela via migration
- **WHEN** `alembic upgrade head` é executado
- **THEN** a tabela `reports` SHALL ser criada com todos os campos e o GIN index em `event_uids`

### Requirement: Status do relatório
O relatório SHALL ter os seguintes status possíveis: EM_ANALISE, COMPLETO, INCOMPLETO, CORRIGINDO, CORRIGIDO, FALHA_CORRECAO. O fluxo de transição SHALL ser: EM_ANALISE → COMPLETO (análise OK) | INCOMPLETO (análise inconclusiva); COMPLETO → CORRIGINDO → CORRIGIDO | FALHA_CORRECAO.

#### Scenario: Criação de relatório EM_ANALISE
- **WHEN** novos eventos são identificados para análise
- **THEN** um relatório SHALL ser criado com status EM_ANALISE, os event_uids dos eventos e markdown vazio

#### Scenario: Análise concluída com sucesso
- **WHEN** o agente conclui a investigação e gera relatório Markdown
- **THEN** o relatório SHALL ser atualizado com o markdown gerado e status COMPLETO

#### Scenario: Análise inconclusiva
- **WHEN** o agente atinge o limite de iterações ou ocorre falha
- **THEN** o relatório SHALL ser atualizado com status INCOMPLETO e o markdown parcial (se disponível)

### Requirement: Relatório Markdown estruturado
O relatório gerado pelo agente SHALL seguir a estrutura: resumo com contagem por severidade (tabela), e para cada problema identificado: severidade (CRITICO/ALTO/MEDIO/BAIXO), namespace, recursos afetados, causa raiz, evidências, solução recomendada e comando sugerido.

#### Scenario: Relatório com múltiplos problemas
- **WHEN** o agente identifica 2 problemas em namespaces diferentes
- **THEN** o relatório SHALL conter resumo com contagem total e seções separadas para cada problema com todos os campos

#### Scenario: Relatório com conteúdo vazio
- **WHEN** o LLM falha em gerar conteúdo
- **THEN** o relatório SHALL ser persistido com markdown vazio e status INCOMPLETO

### Requirement: Configuração do Alembic
O sistema SHALL configurar Alembic com suporte a engine async (asyncpg). O `env.py` SHALL usar `run_async` para rodar migrations. O `alembic.ini` SHALL apontar para a `DATABASE_URL` do projeto.

#### Scenario: Executar migration em banco async
- **WHEN** `alembic upgrade head` é executado
- **THEN** a migration SHALL ser aplicada usando o engine async do projeto
