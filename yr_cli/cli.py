from typing import Optional

import typer

from .commands import now_command, summary_command, weekend_command
from .interface import display_clear_cache

app = typer.Typer()


@app.command()
def now(
    location: Optional[str] = typer.Argument(None),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache and fetch fresh data"
    ),
):
    now_command(
        location=location, limit=limit, country_code=country_code, no_cache=no_cache
    )


@app.command()
def summary(
    location: Optional[str] = typer.Argument(None),
    days: int = typer.Option(5, help="Number of days for summary forecast"),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache and fetch fresh data"
    ),
):
    summary_command(
        location=location,
        days=days,
        limit=limit,
        country_code=country_code,
        no_cache=no_cache,
    )


@app.command()
def weekend(
    location: Optional[str] = typer.Argument(None),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache and fetch fresh data"
    ),
):
    weekend_command(
        location=location, limit=limit, country_code=country_code, no_cache=no_cache
    )


@app.command()
def clear_cache():
    display_clear_cache()


if __name__ == "__main__":
    app()
