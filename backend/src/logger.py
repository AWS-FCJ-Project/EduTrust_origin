import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger("agent")


def log_tool_call(tool_name: str, args: dict, result: str):
    table = Table(title=f"Tool: {tool_name}", show_header=False)
    table.add_row("Args", str(args))
    table.add_row("Result", result[:200] + "..." if len(result) > 200 else result)
    console.print(table)


def log_agent_response(agent_name: str, response: str):
    panel = Panel(Text(response, style="green"), title=agent_name, border_style="blue")
    console.print(panel)


def log_user_input(question: str, conversation_id: str):
    panel = Panel(
        Text(question, style="white"),
        title=f"User Input ({conversation_id})",
        border_style="yellow",
    )
    console.print(panel)


def log_delegation(from_agent: str, to_agent: str, question: str):
    console.print(f"[yellow]{from_agent} -> {to_agent}[/yellow]: {question[:80]}...")
