from typing import Optional

import typer

from .commands import now_command, summary_command, weekend_command
from .interface import display_clear_cache

app = typer.Typer()


@app.command(help="Detailed forecast for the next 24 hours")
def now(
    location: Optional[str] = typer.Argument(None),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache and fetch fresh data"
    ),
    show_map: bool = typer.Option(
        False, "--map", "-m", help="Show a map of the selected location"
    ),
):
    now_command(
        location=location,
        limit=limit,
        country_code=country_code,
        no_cache=no_cache,
        show_map=show_map,
    )


@app.command(help="Summary forecast for the next <days> (default 5) days")
def summary(
    location: Optional[str] = typer.Argument(None),
    days: int = typer.Option(5, help="Number of days for summary forecast"),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache and fetch fresh data"
    ),
    show_map: bool = typer.Option(
        False, "--map", "-m", help="Show a map of the selected location"
    ),
):
    summary_command(
        location=location,
        days=days,
        limit=limit,
        country_code=country_code,
        no_cache=no_cache,
        show_map=show_map,
    )


@app.command(help="Forecast for the next weekend")
def weekend(
    location: Optional[str] = typer.Argument(None),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache and fetch fresh data"
    ),
    show_map: bool = typer.Option(
        False, "--map", "-m", help="Show a map of the selected location"
    ),
):
    weekend_command(
        location=location,
        limit=limit,
        country_code=country_code,
        no_cache=no_cache,
        show_map=show_map,
    )


@app.command(help="Clear the cache of saved locations")
def clear_cache():
    display_clear_cache()


if __name__ == "__main__":
    app()
