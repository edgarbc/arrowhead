"""
CLI entry point for the Arrowhead Obsidian Weekly Hashtag Summarizer.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from .scanner import VaultScanner
from .parser import EntryParser
from .batcher import EntryBatcher
from .summarizer import LLMSummarizer
from .writer import SummaryWriter
from .rag import SummaryRAG
from .utils import setup_logging, parse_date_range

app = typer.Typer(
    name="arrowhead",
    help="Obsidian Weekly Hashtag Summarizer - Automate weekly retrospectives",
    add_completion=False,
)
console = Console()

@app.command()
def summarize(
    vault_path: Path = typer.Argument(
        ...,
        help="Path to your Obsidian vault directory",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    hashtag: str = typer.Option(
        ...,
        "--hashtag",
        "-t",
        help="Hashtag to filter entries (e.g., #meeting, #work)",
    ),
    # ... other options ...
):
    """Generate a weekly summary of Obsidian entries tagged with the specified hashtag."""
    # Implementation here
    pass

@app.command()
def chat(
    summaries_dir: Path = typer.Option(
        None,
        "--summaries",
        "-s",
        help="Directory containing summaries. Defaults to vault/Summaries",
    ),
    model: str = typer.Option(
        "llama2:7b",
        "--model",
        "-m",
        help="LLM model to use for chat",
    ),
):
    """Chat with your summaries using RAG."""
    # Implementation here
    pass

@app.command()
def scan(
    vault_path: Path = typer.Argument(
        ...,
        help="Path to your Obsidian vault directory",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    hashtag: Optional[str] = typer.Option(
        None,
        "--hashtag",
        "-t",
        help="Optional hashtag to filter entries",
    ),
):
    """Scan vault and show available entries (useful for testing)."""
    # Implementation here
    pass

if __name__ == "__main__":
    app()