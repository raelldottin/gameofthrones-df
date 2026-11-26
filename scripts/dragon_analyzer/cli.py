"""CLI: explicit failure for unsupported extraction; actual schema validation."""
from pathlib import Path
from typing import Optional

import typer

from .analyzer import DragonAnalyzer
from .models import ArmyComposition, DragonData

app = typer.Typer(help="Game of Thrones Dragonfire evidence analyzer")


def _worker(output: Optional[str]) -> DragonAnalyzer:
    return DragonAnalyzer(Path(output) if output is not None else None)


def _fail(exc: Exception) -> None:
    typer.echo(f"Error: {exc}", err=True)
    raise typer.Exit(code=1)


@app.command()
def analyze(
    image_path: str,
    output: Optional[str] = typer.Option(None, "--output", "-o"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Read a screenshot into isolated observation storage."""
    try:
        result = _worker(output).analyze_screenshot(Path(image_path))
        typer.echo(result.model_dump_json())
    except (OSError, ValueError, RuntimeError, TypeError) as exc:
        _fail(exc)


@app.command()
def batch(
    directory: str,
    pattern: str = typer.Option("IMG_*", "--pattern", "-p"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Read matching screenshots; fail on a rejected observation."""
    try:
        results = _worker(output).batch_analyze(Path(directory), pattern)
        typer.echo(f"Recorded {len(results)} observations")
    except (OSError, ValueError, RuntimeError, TypeError) as exc:
        _fail(exc)


@app.command()
def validate(
    data_file: str,
    schema: str = typer.Option("dragon", "--schema", "-s"),
):
    """Validate a legacy DragonData or ArmyComposition JSON document."""
    schemas = {"dragon": DragonData, "army": ArmyComposition}
    if schema not in schemas:
        _fail(ValueError(f"Unknown schema: {schema}"))
    try:
        schemas[schema].model_validate_json(Path(data_file).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(exc)
    typer.echo("Valid")


if __name__ == "__main__":
    app()
