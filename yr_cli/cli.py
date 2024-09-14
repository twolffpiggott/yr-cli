from datetime import date, datetime, timedelta, timezone
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


@app.command()
def now(
    location: Optional[str] = typer.Argument(None),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache and fetch fresh data"
    ),
):
    if location is None:
        location = prompt_location()

    if no_cache:
        selected_location = get_location(location, limit, country_code)
    else:
        cached_location = cache.get_cached_location(location)
        if cached_location:
            selected_location = cached_location
        else:
            selected_location = get_location(location, limit, country_code)
            cache.cache_location(location, selected_location)

    if not selected_location:
        return

    yr_client = yr_weather.Locationforecast(headers=USER_AGENT_HEADER)
    forecast = yr_client.get_forecast(
        lat=float(selected_location["lat"]), lon=float(selected_location["lon"])
    )

    now = datetime.now().astimezone()
    end_time = now + timedelta(hours=24)

    location_text = Text()
    location_text.append("📍 ", style="bold green")
    location_text.append(selected_location["name"], style="bold")

    content = Group(location_text, "")

    current_day = now.date()
    weather_table = create_weather_table(current_day)

    while now < end_time:
        now = now.replace(minute=0, second=0, microsecond=0)
        if now.date() != current_day:
            if weather_table:
                content.renderables.append(weather_table)
            current_day = now.date()
            weather_table = create_weather_table(current_day)

        forecast_data = forecast.get_forecast_time(now.astimezone(timezone.utc))
        summary = forecast_data.next_hour.summary.symbol_code.replace("_", " ").title()
        temp = f"{forecast_data.details.air_temperature:.1f}°C"
        precipitation_amount = forecast_data.next_hour.details.precipitation_amount
        rain = "" if float(precipitation_amount) == 0 else f"{precipitation_amount} mm"
        wind = f"{forecast_data.details.wind_speed:.1f} m/s"
        cloud = f"{forecast_data.details.cloud_area_fraction:.0f}%"

        time_str = "Now" if now == datetime.now().astimezone() else now.strftime("%H")

        weather_table.add_row(time_str, summary, temp, rain, wind, cloud)

        now += timedelta(hours=1)

    if weather_table:
        content.renderables.append(weather_table)

    weather_panel = Panel(
        content,
        title="[bold blue]24-Hour Weather Forecast[/bold blue]",
        expand=False,
        border_style="blue",
    )

    console.print(weather_panel)


@app.command()
def summary(
    location: Optional[str] = typer.Argument(None),
    days: Optional[int] = typer.Option(3, help="Number of days for summary forecast"),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass cache and fetch fresh data"
    ),
):
    if location is None:
        location = prompt_location()

    if no_cache:
        selected_location = get_location(location, limit, country_code)
    else:
        cached_location = cache.get_cached_location(location)
        if cached_location:
            selected_location = cached_location
        else:
            selected_location = get_location(location, limit, country_code)
            cache.cache_location(location, selected_location)

    if not selected_location:
        return

    yr_client = yr_weather.Locationforecast(headers=USER_AGENT_HEADER)
    forecast = yr_client.get_forecast(
        lat=float(selected_location["lat"]), lon=float(selected_location["lon"])
    )

    location_text = Text()
    location_text.append("📍 ", style="bold green")
    location_text.append(selected_location["name"], style="bold")
    content = Group(location_text, "")

    now = datetime.now().astimezone()
    for day in range(days):
        forecast_times = [
            now.replace(hour=hour, minute=0, second=0, microsecond=0)
            + timedelta(days=day)
            for hour in [2, 8, 14, 20]
        ]
        weather_table = create_weather_table(forecast_times[0].date())
        for forecast_time in forecast_times:
            if forecast_time < now:
                continue
            forecast_data = forecast.get_forecast_time(
                forecast_time.astimezone(timezone.utc)
            )
            summary = forecast_data.next_6_hours.summary.symbol_code.replace(
                "_", " "
            ).title()
            temp = f"{forecast_data.details.air_temperature:.1f}°C"
            precipitation_amount = (
                forecast_data.next_6_hours.details.precipitation_amount
            )
            rain = (
                "" if float(precipitation_amount) == 0 else f"{precipitation_amount} mm"
            )
            wind = f"{forecast_data.details.wind_speed:.1f} m/s"
            cloud = f"{forecast_data.details.cloud_area_fraction:.0f}%"
            time_str = f"{_get_24_hr_fmt(forecast_time.hour)}-{_get_24_hr_fmt(forecast_time.hour+6)}"
            weather_table.add_row(time_str, summary, temp, rain, wind, cloud)
        content.renderables.append(weather_table)

    weather_panel = Panel(
        content,
        title="[bold blue]Summary Weather Forecast[/bold blue]",
        expand=False,
        border_style="blue",
    )

    console.print(weather_panel)


def _get_24_hr_fmt(hour: int) -> str:
    return f"{hour%24:0>2}"


@app.command()
def clear_cache():
    """Clear the entire location cache."""
    if cache.clear_cache():
        console.print("[bold green]Cache cleared successfully![/bold green]")
    else:
        console.print("[bold red]Failed to clear cache.[/bold red]")


if __name__ == "__main__":
    app()
