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
    week_start: Optional[str] = typer.Option(None, "--week-start"),
    week_end: Optional[str] = typer.Option(None, "--week-end"),
    model: str = typer.Option("llama2:7b", "--model", "-m"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o"),
    # ... other options ...
):
    """Generate a weekly summary of Obsidian entries tagged with the specified hashtag."""
    
    try:
        console.print(f"Starting summary generation for {hashtag} from {week_start} to {week_end} with model {model}")
        console.print(f"Output directory: {output_dir}")

        # setup logging
        setup_logging()

        # parse date range
        if week_start and week_end:
            week_start = parse_date_range(week_start, week_end)
        else:
            week_start = datetime.now() - timedelta(days=7)
            week_end = datetime.now()

        # scan vault
        with console.status("[bold green]Scanning vault...[/bold green]"):
            scanner = VaultScanner(vault_path)
            scan_results = scanner.scan(hashtag, week_start, week_end)

        # parse entries
        with console.status("[bold green]Parsing entries...[/bold green]"):
            parser = EntryParser()
            parsed_entries = parser.parse(scan_results.markdown_files, hashtag)

            if not parsed_entries:
                console.print("[bold yellow]No entries found with hashtag {hashtag}[/bold yellow]")
                raise typer.Exit(0)
        
        # filter by date range
        if week_start and week_end:
            parsed_entries = [entry for entry in parsed_entries if entry.date >= week_start and entry.date <= week_end]
            console.print(f"[bold blue]Filtered to {len(parsed_entries)} entries in date range[/bold blue]")

        # batch entries
        with console.status("[bold green]Batching entries...[/bold green]"):
            batcher = EntryBatcher()
            batched_entries = batcher.create_batches(parsed_entries)

        # summarize batches
        with console.status("[bold green]Summarizing entries...[/bold green]"):
            summarizer = LLMSummarizer(model, batch_size=10)
            summaries = []
            
            with Progress() as progress:
                task = progress.add_task("[cyan]Summarizing batches...[/cyan]", total=len(batched_entries))

                for i, batch in enumerate(batched_entries):
                    response = summarizer.summarize_batch(
                        batch, hashtag, start_date, end_date, 
                        batch_index=i+1, 
                        total_batches=len(batched_entries),
                        progress=progress
                    )
                    summaries.append(response)
                    progress.update(task, completed=i+1)
                    
        # combine summaries
        with console.status("[bold green]Combining summaries...[/bold green]"):
            output_path = output_dir or Path(vault_path) / "Summaries"
            writer = SummaryWriter(output_path)
            output_file = writer.write_combined_summary(summaries, hashtag, week_start, week_end)
            console.print(f"[bold green]Combined summary written to {output_file}[/bold green]")
            
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)

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