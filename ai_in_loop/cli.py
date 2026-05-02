"""CLI for the paper analyzer workflow.

This module provides the `analyze` command for processing academic papers
from arXiv URLs or DOIs.

Usage:
    python -m ai_in_loop.cli analyze <url> --format json|markdown --verbose --output file.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console

from .config import Config
from .graph import analyze_paper, get_graph_image
from .output import format_output

console = Console()
app = typer.Typer(help="Paper Analyzer CLI")


@app.command()
def analyze(
    url: str = typer.Argument(
        ...,
        help="arXiv URL or DOI to analyze (e.g., https://arxiv.org/abs/1706.03762)",
    ),
    fmt: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: json or markdown",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed progress information",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to file instead of stdout",
    ),
) -> None:
    """Analyze an academic paper from an arXiv URL or DOI.

    Fetches paper metadata from academic APIs, finds open access full text
    when available, and generates a summary using an LLM.

    Examples:
        python -m ai_in_loop.cli analyze "https://arxiv.org/abs/1706.03762"
        python -m ai_in_loop.cli analyze "https://arxiv.org/abs/1706.03762" --format json
        python -m ai_in_loop.cli analyze "10.1038/nature12373" --verbose
        python -m ai_in_loop.cli analyze "https://arxiv.org/abs/1706.03762" -o result.json
    """
    load_dotenv()
    cfg = Config.from_env()

    if verbose:
        console.print(f"[dim]Analyzing: {url}[/dim]")
        console.print(f"[dim]Using LLM: {'Gemini' if cfg.use_gemini else 'Mock'}[/dim]")

    # Run the analysis workflow
    if verbose:
        console.print("[dim]Running workflow...[/dim]")

    result = analyze_paper(url, cfg)

    if verbose:
        warnings = result.get("warnings", [])
        if warnings:
            console.print(f"[yellow]Warnings: {len(warnings)}[/yellow]")
            for w in warnings:
                console.print(f"[yellow]  - {w}[/yellow]")

    # Format output
    try:
        output_text = format_output(result, fmt)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    # Write to file or stdout
    if output:
        output_path = Path(output)
        output_path.write_text(output_text, encoding="utf-8")
        if verbose:
            console.print(f"[green]Output written to: {output_path}[/green]")
    else:
        console.print(output_text)


@app.command()
def visualize(
    output_path: str = typer.Argument(
        "workflow.png",
        help="Path to save the workflow visualization",
    ),
) -> None:
    """Generate a visualization of the workflow graph.

    Creates a PNG image showing the workflow structure with nodes and edges.

    Example:
        python -m ai_in_loop.cli visualize workflow.png
    """
    load_dotenv()
    cfg = Config.from_env()

    console.print(f"[dim]Generating workflow visualization...[/dim]")

    image_bytes = get_graph_image(cfg, output_path)

    if image_bytes:
        console.print(f"[green]Visualization saved to: {output_path}[/green]")
    else:
        console.print("[red]Error: Could not generate visualization.[/red]")
        console.print("[dim]Make sure you have the required dependencies installed:[/dim]")
        console.print("[dim]  pip install grandalf[/dim]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
