from datetime import date, datetime
from functools import wraps
from typing import Callable, Dict, List, Optional

import inquirer
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.traceback import install

from .api import get_openstreetmap_locations
from .cache import cache_location, clear_cache, get_cached_location

console = Console()


def create_weather_table(current_day: date, width: int = 80) -> Table:
    weather_table = Table(
        box=box.ROUNDED,
        expand=False,
        show_header=True,
        title=f"[bold blue]{current_day.strftime('%A %d. %B')}[/bold blue]",
        width=width,
    )
    weather_table.add_column("Time", style="cyan", no_wrap=True)
    weather_table.add_column("Summary", style="yellow")
    weather_table.add_column("Temp", style="red", no_wrap=True)
    weather_table.add_column("Rain", style="blue", no_wrap=True)
    weather_table.add_column("Wind", style="green", no_wrap=True)
    weather_table.add_column("Cloud", style="magenta", no_wrap=True)
    return weather_table


def get_selected_location(
    location: Optional[str],
    limit: int,
    country_code: str,
    no_cache: bool,
) -> Optional[dict]:
    if location is None:
        location = prompt_location()
    if no_cache:
        selected_location = get_location(location, limit, country_code)
    else:
        cached_location = get_cached_location(location)
        if cached_location:
            selected_location = cached_location
        else:
            selected_location = get_location(location, limit, country_code)
            if selected_location:
                cache_location(location, selected_location)
    return selected_location


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


def get_location(query: str, limit: int, country_code: str) -> Optional[dict]:
    locations = get_openstreetmap_locations(query, limit, country_code)
    if not locations:
        console.print("[bold red]Error:[/bold red] No locations found.")
        return None
    if len(locations) > 1:
        selected_location = select_location(locations)
    else:
        selected_location = locations[0]
    return selected_location


def display_weather(
    forecast_timesteps: Dict[datetime, dict],
    selected_location: dict,
    panel_title: str,
):
    current_day = min(forecast_timesteps).date()
    location_text = Text()
    location_text.append("📍 ", style="bold green")
    location_text.append(selected_location["name"], style="bold")
    content = Group(location_text, "")
    weather_table = create_weather_table(current_day)
    for forecast_time, data in forecast_timesteps.items():
        if forecast_time.date() != current_day:
            current_day = forecast_time.date()
            if weather_table.rows:
                content.renderables.append(weather_table)
                weather_table = create_weather_table(current_day)
        summary = data["symbol_code"].replace("_", " ").title()
        temp = f"{data['air_temperature']:.1f}°C"
        precipitation_amount = data["precipitation_amount"]
        rain = "" if float(precipitation_amount) == 0 else f"{precipitation_amount} mm"
        wind = f"{data['wind_speed']:.1f} m/s"
        cloud = f"{data['cloud_area_fraction']:.0f}%"
        time_str = f"{_get_24_hr_fmt(forecast_time.hour)}"
        weather_table.add_row(time_str, summary, temp, rain, wind, cloud)
    if weather_table.rows:
        content.renderables.append(weather_table)

    weather_panel = Panel(
        content,
        title=f"[bold blue]{panel_title}[/bold blue]",
        expand=False,
        border_style="blue",
    )

    console.print(weather_panel)


def display_clear_cache():
    if clear_cache():
        console.print("[bold green]Cache cleared successfully![/bold green]")
    else:
        console.print("[bold red]Failed to clear cache.[/bold red]")


def handle_command_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            install(max_frames=1)
            raise

    return wrapper


def _get_24_hr_fmt(hour: int) -> str:
    return f"{hour%24:0>2}"
