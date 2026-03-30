## 1. Modelo de Dados

- [x] 1.1 Adicionar campo `fix_result` (Text, nullable) ao modelo `Report` em `models/report.py`
- [x] 1.2 Gerar migration Alembic para adicionar coluna `fix_result` à tabela `reports`

## 2. Agente de Correção

- [x] 2.1 Criar arquivo de prompt `agents/prompts/fix.md` com instruções ReAct e regras de segurança
- [x] 2.2 Implementar `agents/fix_agent.py` com função `execute_fix(report_markdown: str) -> tuple[str, str]` que retorna (resultado, status)

## 3. Endpoint API

- [x] 3.1 Implementar endpoint `POST /api/reports/{id}/fix` em `api/router.py` com validação de status, atualização para CORRIGINDO e retorno 202
- [x] 3.2 Implementar task background que executa o agente, persiste `fix_result`, atualiza status e notifica Discord

## 4. Interface Web

- [x] 4.1 Habilitar botão "Executar correção" no template para fazer POST via JavaScript para `/api/reports/{id}/fix`
- [x] 4.2 Adicionar seção "Resultado da Correção" na página de detalhe para exibir `fix_result` renderizado em HTML
- [x] 4.3 Atualizar rota `report_detail` em `web/router.py` para converter `fix_result` Markdown em HTML e passar ao template
