"""Generate a diagram for the current LangGraph workflow.

This script reads the workflow from ai_in_loop.graph.build_graph so the
diagram always matches the implemented routing logic.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from ai_in_loop.config import Config
from ai_in_loop.graph import build_graph


def generate_workflow_graph(output_path: Path, save_png: bool) -> tuple[Path, Path | None]:
    """Write the workflow graph as Mermaid text and optionally as a PNG."""

    load_dotenv()
    cfg = Config.from_env()
    graph = build_graph(cfg).get_graph()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(graph.draw_mermaid(), encoding="utf-8")

    png_path: Path | None = None
    if save_png:
        png_path = output_path.with_suffix(".png")
        png_path.write_bytes(graph.draw_mermaid_png())

    return output_path, png_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Mermaid diagram for the current workflow.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/workflow_graph.mmd"),
        help="Path for the Mermaid graph output.",
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="Also save a PNG next to the Mermaid file.",
    )
    args = parser.parse_args()

    mermaid_path, png_path = generate_workflow_graph(args.output, args.png)
    print(f"Mermaid graph written to {mermaid_path}")
    if png_path is not None:
        print(f"PNG graph written to {png_path}")


if __name__ == "__main__":
    main()