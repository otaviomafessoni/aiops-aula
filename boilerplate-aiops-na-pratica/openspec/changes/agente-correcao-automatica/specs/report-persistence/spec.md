## MODIFIED Requirements

### Requirement: Modelo de dados Report
O sistema SHALL criar uma tabela `reports` no PostgreSQL com os campos: `id` (UUID, PK), `markdown` (TEXT), `status` (VARCHAR), `event_uids` (TEXT[] com GIN index), `fix_result` (TEXT, nullable), `created_at` (TIMESTAMP WITH TIME ZONE) e `updated_at` (TIMESTAMP WITH TIME ZONE). A migration SHALL ser gerenciada via Alembic.

#### Scenario: Criação da tabela via migration
- **WHEN** `alembic upgrade head` é executado
- **THEN** a tabela `reports` SHALL ser criada com todos os campos incluindo `fix_result` e o GIN index em `event_uids`

#### Scenario: Migration de adição do campo fix_result
- **WHEN** `alembic upgrade head` é executado em banco existente sem o campo `fix_result`
- **THEN** o campo `fix_result` (TEXT, nullable) SHALL ser adicionado à tabela `reports`
