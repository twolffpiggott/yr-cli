from typing import List, Optional
from urllib.parse import quote_plus

import inquirer
import requests
import typer
import yr_weather
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import cache

app = typer.Typer()
console = Console()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT_HEADER = {"User-Agent": "YrCLI/0.1 github.com/yr-cli"}


def get_locations(query: str, limit: int, country_code: str) -> List[dict]:
    encoded_query = quote_plus(query)
    params = {
        "q": encoded_query,
        "format": "json",
        "limit": limit,
        "countrycodes": country_code,
    }
    response = requests.get(NOMINATIM_URL, params=params, headers=USER_AGENT_HEADER)
    return response.json()


def prompt_location() -> str:
    questions = [inquirer.Text("location", message="Enter a location")]
    answers = inquirer.prompt(questions)
    return answers["location"]


def select_location(locations: List[dict]) -> dict:
    choices = [(f"{loc['display_name']}", loc) for loc in locations]
    questions = [
        inquirer.List(
            "location", message="Confirm the location", choices=choices, carousel=True
        )
    ]
    answers = inquirer.prompt(questions)
    return answers["location"]


def get_location(query: str, limit: int, country_code: str):
    locations = get_locations(query, limit, country_code)
    if not locations:
        console.print("[bold red]Error:[/bold red] No locations found.")
        return
    if len(locations) > 1:
        selected_location = select_location(locations)
    else:
        selected_location = locations[0]
    return selected_location


@app.command()
def weather(
    location: Optional[str] = typer.Argument(None),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache and fetch fresh data"
    ),
):
    if location is None:
        location = prompt_location()

    if not no_cache:
        cached_location = cache.get_cached_location(location)
        if cached_location:
            selected_location = cached_location
        else:
            selected_location = get_location(location, limit, country_code)
            cache.cache_location(location, selected_location)
    else:
        selected_location = get_location(location, limit, country_code)

    yr_client = yr_weather.Locationforecast(headers=USER_AGENT_HEADER)
    forecast = yr_client.get_forecast(
        lat=float(selected_location["lat"]), lon=float(selected_location["lon"])
    )
    current_hour = forecast.now()
    temp = current_hour.details.air_temperature
    rain = current_hour.next_hour.details.precipitation_amount
    wind_speed = current_hour.details.wind_speed
    cloud_area_fraction = current_hour.details.cloud_area_fraction
    summary = current_hour.next_hour.summary.symbol_code

    weather_table = Table(box=box.ROUNDED, expand=False, show_header=False)
    weather_table.add_column("Property", style="cyan", no_wrap=True)
    weather_table.add_column("Value", style="yellow")

    weather_table.add_row("🌡️ Temperature", f"{temp}°C")
    weather_table.add_row("🌦️ Summary", summary.replace("_", " ").title())
    weather_table.add_row("🌧️ Rain (next hour)", f"{rain} mm")
    weather_table.add_row("💨 Wind speed", f"{wind_speed} m/s")
    weather_table.add_row("☁️ Cloud cover", f"{cloud_area_fraction}%")

    location_text = Text()
    location_text.append("📍 ", style="bold green")
    location_text.append(selected_location["display_name"], style="bold")

    content = Group(location_text, "", weather_table)

    weather_panel = Panel(
        content,
        title="[bold blue]Weather Information[/bold blue]",
        expand=False,
        border_style="blue",
    )

    console.print(weather_panel)


@app.command()
def clear_cache():
    """Clear the entire location cache."""
    if cache.clear_cache():
        console.print("[bold green]Cache cleared successfully![/bold green]")
    else:
        console.print("[bold red]Failed to clear cache.[/bold red]")


if __name__ == "__main__":
    app()
