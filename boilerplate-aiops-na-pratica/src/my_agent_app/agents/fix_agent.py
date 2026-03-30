import asyncio
import logging
import os
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware, ToolRetryMiddleware
from langchain_anthropic import ChatAnthropic

from my_agent_app.agents.mcp_kubernetes import get_kubernetes_tools

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITERATIONS = 25
MAX_RETRIES = 3
BACKOFF_BASE = 1
POST_FIX_WAIT_SECONDS = 15

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt() -> str:
    return (PROMPTS_DIR / "fix.md").read_text(encoding="utf-8")


def _get_max_iterations() -> int:
    raw = os.environ.get("AGENT_MAX_ITERATIONS")
    if raw is None:
        return DEFAULT_MAX_ITERATIONS
    try:
        value = int(raw)
        if value <= 0:
            raise ValueError("must be positive")
        return value
    except (ValueError, TypeError):
        logger.warning(
            "AGENT_MAX_ITERATIONS='%s' inválido, usando padrão %d",
            raw,
            DEFAULT_MAX_ITERATIONS,
        )
        return DEFAULT_MAX_ITERATIONS


def _extract_content(msg) -> str:
    """Extrai texto de uma mensagem LangChain, tratando content como str ou lista."""
    if not hasattr(msg, "content"):
        return ""
    content = msg.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def _parse_fix_result(response: str) -> tuple[str, str]:
    """Interpreta a resposta do agente e retorna (resultado_completo, status).

    Status: 'CORRIGIDO' ou 'FALHA_CORRECAO'.
    """
    upper = response.upper()

    if "CORRIGIDO" in upper:
        return response, "CORRIGIDO"
    elif "FALHA" in upper:
        return response, "FALHA_CORRECAO"
    else:
        logger.warning(
            "Resposta do agente de correção não contém 'CORRIGIDO' nem 'FALHA'. Primeiros 200 chars: '%s'",
            response[:200],
        )
        return response, "FALHA_CORRECAO"


async def execute_fix(report_markdown: str) -> tuple[str, str]:
    """Executa correção automática no cluster baseada no relatório de análise.

    Returns:
        Tupla (resultado_markdown, status).
        status é 'CORRIGIDO' ou 'FALHA_CORRECAO'.
    """
    max_iterations = _get_max_iterations()
    prompt_template = _load_prompt()

    system_prompt = prompt_template.replace("{report_markdown}", report_markdown)

    user_message = "Execute as correções descritas no relatório acima, seguindo o padrão ReAct."

    model = ChatAnthropic(model="claude-haiku-4-5-20251001")
    tools = await get_kubernetes_tools()

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[
            ToolCallLimitMiddleware(
                run_limit=max_iterations,
                exit_behavior="continue",
            ),
            ToolRetryMiddleware(
                max_retries=2,
                on_failure="continue",
            ),
        ],
    )

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": user_message}]}
            )
            break
        except Exception as e:
            last_error = e
            wait = BACKOFF_BASE * (2 ** attempt)
            logger.warning(
                "Erro na API Claude durante correção (tentativa %d/%d). Retry em %ds.",
                attempt + 1,
                MAX_RETRIES,
                wait,
                exc_info=True,
            )
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(wait)
    else:
        logger.error("Falha na API Claude após %d tentativas", MAX_RETRIES)
        return f"Erro: falha na API Claude após {MAX_RETRIES} tentativas. Último erro: {last_error}", "FALHA_CORRECAO"

    messages = result.get("messages", [])

    response = ""
    for msg in reversed(messages):
        text = _extract_content(msg)
        if text.strip():
            response = text
            break

    if not response:
        return "Erro: agente não gerou resposta", "FALHA_CORRECAO"

    return _parse_fix_result(response)
