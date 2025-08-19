"""
CLI entry point for the Arrowhead Obsidian Weekly Hashtag Summarizer.
"""

import typer # for CLI
from pathlib import Path # for file paths
from typing import Optional # for type hints
from rich.console import Console
from rich.progress import Progress # for progress bars
from rich.panel import Panel # for panels

# local imports
from .scanner import VaultScanner # for scanning the vault
from .parser import EntryParser # for parsing the entries
from .batcher import EntryBatcher # for batching the entries
from .summarizer import LLMSummarizer # for summarizing the entries
from .writer import SummaryWriter # for writing the summaries
from .rag import SummaryRAG # for RAG
from .utils import setup_logging, parse_date_range # for logging and date parsing

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
    try:
        console.print(f"Starting chat with model {model} and summaries in {summaries_dir}")
        
        if summaries_dir is None:
            console.print("[red]Error: Please specify --summaries directory")
            raise typer.Exit(1)
        
        # setup RAG
        rag = SummaryRAG(summaries_dir, model)
        
        # chat loop
        console.print("[green]💬 Chat with your summaries (type 'quit' to exit)[/green]")
        
        while True:
            try:
                message = console.input("[cyan]You: ")
                if message.lower() in ['quit', 'exit', 'q']:
                    break
                
                response = rag.chat(message)
                console.print(f"[green]Assistant: {response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}")
                
    except Exception as e:
        console.print(f"[red]❌ Error: {e}")
        raise typer.Exit(1)

@app.command()
def scan(
    vault_path: Path = typer.Argument(
        ...,
        help="Path to your Obsidian vault directory",
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
    try:
        # manual validation
        if not vault_path.exists():
            console.print(f"[red]❌ Error: Vault path does not exist: {vault_path}")
            raise typer.Exit(1)
        
        if not vault_path.is_dir():
            console.print(f"[red]❌ Error: Vault path is not a directory: {vault_path}")
            raise typer.Exit(1)

        # Scan vault
        scanner = VaultScanner(vault_path)
        scan_result = scanner.scan()
        
        console.print(f"[blue]�� Vault: {vault_path}")
        console.print(f"[blue]📄 Found {len(scan_result.markdown_files)} markdown files")
        
        if hashtag:
            # Parse and filter by hashtag
            parser = EntryParser()
            entries = parser.parse_files(scan_result.markdown_files, hashtag)
            
            console.print(f"[green]✅ Found {len(entries)} entries with #{hashtag}")
            
            for entry in entries[:10]:  # Show first 10
                console.print(f"  📝 {entry.file_path.name} ({entry.date})")
            
            if len(entries) > 10:
                console.print(f"  ... and {len(entries) - 10} more")
        else:
            # Show all files
            for file_path in scan_result.markdown_files[:20]:
                console.print(f"  📄 {file_path.relative_to(vault_path)}")
            
            if len(scan_result.markdown_files) > 20:
                console.print(f"  ... and {len(scan_result.markdown_files) - 20} more")
                
    except Exception as e:
        console.print(f"[red]❌ Error: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()