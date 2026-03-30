import os

from langchain_mcp_adapters.client import MultiServerMCPClient

DEFAULT_MCP_URL = "http://localhost:3001/mcp"


def get_mcp_url() -> str:
    return os.environ.get("MCP_KUBERNETES_URL", DEFAULT_MCP_URL)


def create_kubernetes_mcp_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "kubernetes": {
                "transport": "streamable_http",
                "url": get_mcp_url(),
            }
        }
    )


async def get_kubernetes_tools() -> list:
    client = create_kubernetes_mcp_client()
    return await client.get_tools()
