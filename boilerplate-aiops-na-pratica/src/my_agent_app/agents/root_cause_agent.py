import json
import logging
import os
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware, ToolRetryMiddleware
from langchain_anthropic import ChatAnthropic

from my_agent_app.agents.mcp_kubernetes import get_kubernetes_tools

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITERATIONS = 25

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt() -> str:
    return (PROMPTS_DIR / "root_cause_analysis.md").read_text(encoding="utf-8")


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


async def analyze_events(events: list[dict]) -> tuple[str, bool]:
    """Executa análise de causa raiz dos eventos via agente LangChain + MCP.

    Returns:
        Tupla (markdown_do_relatorio, is_complete).
        is_complete=True se a análise concluiu normalmente,
        False se atingiu o limite de iterações.
    """
    max_iterations = _get_max_iterations()
    system_prompt = _load_prompt()

    events_text = json.dumps(events, ensure_ascii=False, indent=2)
    user_message = f"Analise os seguintes eventos Warning do Kubernetes e gere um relatório de causa raiz:\n\n```json\n{events_text}\n```"

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

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_message}]}
    )

    messages = result.get("messages", [])

    markdown = ""
    for msg in reversed(messages):
        if not hasattr(msg, "content"):
            continue
        content = msg.content
        if isinstance(content, list):
            content = "\n".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        if isinstance(content, str) and content.strip():
            markdown = content
            break

    is_complete = "inconclusiva" not in markdown.lower() and "análise manual" not in markdown.lower()

    return markdown, is_complete
