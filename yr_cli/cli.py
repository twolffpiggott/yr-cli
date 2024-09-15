from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

import inquirer
import requests
import typer
from requests_cache import CachedSession
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import cache
from .locationforecast.data import filter_location_forecast
from .locationforecast.type import METJSONForecast

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


def get_location_forecast(lat: int, lon: int) -> METJSONForecast:
    session = CachedSession(
        (Path.home() / ".met_cache.sqlite").as_posix(),
        cache_control=True,
        expire_after=timedelta(days=1),
    )
    response = session.get(
        f"https://api.met.no/weatherapi/locationforecast/2.0/complete?lat={lat}&lon={lon}",
        headers=USER_AGENT_HEADER,
    )
    response.raise_for_status()
    location_forecast: METJSONForecast = response.json()
    return location_forecast


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


def get_location(query: str, limit: int, country_code: str) -> str:
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

    forecast: METJSONForecast = get_location_forecast(
        lat=float(selected_location["lat"]), lon=float(selected_location["lon"])
    )

    now = datetime.now().astimezone()
    start_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    time_series = [start_time + timedelta(hours=hours) for hours in range(25)]
    filtered_forecast_timesteps = filter_location_forecast(
        forecast,
        time_series,
        keys=[
            ["next_6_hours", "summary", "symbol_code"],
            ["instant", "details", "air_temperature"],
            ["next_6_hours", "details", "precipitation_amount"],
            ["instant", "details", "wind_speed"],
            ["instant", "details", "cloud_area_fraction"],
        ],
    )

    current_day = time_series[0].date()
    location_text = Text()
    location_text.append("📍 ", style="bold green")
    location_text.append(selected_location["name"], style="bold")
    content = Group(location_text, "")
    weather_table = create_weather_table(current_day)
    for forecast_timestep_time, filtered_data in filtered_forecast_timesteps.items():
        if forecast_timestep_time.date() != current_day:
            current_day = forecast_timestep_time.date()
            if weather_table.rows:
                content.renderables.append(weather_table)
                weather_table = create_weather_table(current_day)
        summary = filtered_data["symbol_code"].replace("_", " ").title()
        temp = f"{filtered_data['air_temperature']:.1f}°C"
        precipitation_amount = filtered_data["precipitation_amount"]
        rain = "" if float(precipitation_amount) == 0 else f"{precipitation_amount} mm"
        wind = f"{filtered_data['wind_speed']:.1f} m/s"
        cloud = f"{filtered_data['cloud_area_fraction']:.0f}%"
        time_str = f"{_get_24_hr_fmt(forecast_timestep_time.hour)}"
        weather_table.add_row(time_str, summary, temp, rain, wind, cloud)
    if weather_table.rows:
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
    days: Optional[int] = typer.Option(5, help="Number of days for summary forecast"),
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

    forecast: METJSONForecast = get_location_forecast(
        lat=float(selected_location["lat"]), lon=float(selected_location["lon"])
    )

    now = datetime.now().astimezone()
    utc_now = now.astimezone(timezone.utc)
    utc_start_time = utc_now.replace(minute=0, second=0, microsecond=0) + timedelta(
        hours=1
    )
    utc_start_hour = utc_start_time.hour
    time_series = []
    for day in range(days):
        hours = [0, 6, 12, 18]
        if day == 0:
            hours = [utc_start_hour] + [hour for hour in hours if hour > utc_start_hour]
        time_series.extend(
            [
                utc_start_time.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                ).astimezone()
                + timedelta(days=day)
                for hour in hours
            ]
        )
    filtered_forecast_timesteps = filter_location_forecast(
        forecast,
        time_series,
        keys=[
            ["next_6_hours", "summary", "symbol_code"],
            ["instant", "details", "air_temperature"],
            ["next_6_hours", "details", "precipitation_amount"],
            ["instant", "details", "wind_speed"],
            ["instant", "details", "cloud_area_fraction"],
        ],
    )

    location_text = Text()
    location_text.append("📍 ", style="bold green")
    location_text.append(selected_location["name"], style="bold")
    content = Group(location_text, "")
    current_day = time_series[0].date()
    location_text = Text()
    location_text.append("📍 ", style="bold green")
    location_text.append(selected_location["name"], style="bold")
    content = Group(location_text, "")
    weather_table = create_weather_table(current_day)
    for forecast_timestep_time, filtered_data in filtered_forecast_timesteps.items():
        if forecast_timestep_time.date() != current_day:
            current_day = forecast_timestep_time.date()
            if weather_table.rows:
                content.renderables.append(weather_table)
                weather_table = create_weather_table(current_day)
        summary = filtered_data["symbol_code"].replace("_", " ").title()
        temp = f"{filtered_data['air_temperature']:.1f}°C"
        precipitation_amount = filtered_data["precipitation_amount"]
        rain = "" if float(precipitation_amount) == 0 else f"{precipitation_amount} mm"
        wind = f"{filtered_data['wind_speed']:.1f} m/s"
        cloud = f"{filtered_data['cloud_area_fraction']:.0f}%"
        time_str = f"{_get_24_hr_fmt(forecast_timestep_time.hour)}"
        weather_table.add_row(time_str, summary, temp, rain, wind, cloud)
    if weather_table.rows:
        content.renderables.append(weather_table)

    weather_panel = Panel(
        content,
        title="[bold blue]Summary Weather Forecast[/bold blue]",
        expand=False,
        border_style="blue",
    )

    console.print(weather_panel)


@app.command()
def weekend(
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

    forecast: METJSONForecast = get_location_forecast(
        lat=float(selected_location["lat"]), lon=float(selected_location["lon"])
    )

    now = datetime.now().astimezone()
    start_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    time_series = []
    current_day = now.date()
    days_ahead = 4 - current_day.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    start_time = start_time + timedelta(days=days_ahead)
    utc_start_time = start_time.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    ) + timedelta(hours=1)
    utc_start_hour = utc_start_time.hour
    hours = list(range(24))
    utc_summary_hours = [0, 6, 12, 18]
    for day in range(3):
        if days_ahead <= 2:
            if days_ahead == 0:
                hours = [utc_start_hour] + [
                    hour for hour in hours if hour > utc_start_hour
                ]
            hours_for_day = [
                start_time.replace(hour=hour, minute=0, second=0, microsecond=0)
                + timedelta(days=day)
                for hour in hours
            ]
        else:
            hours_for_day = [
                utc_start_time.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                ).astimezone()
                + timedelta(days=day)
                for hour in utc_summary_hours
            ]
        time_series.extend(hours_for_day)
    filtered_forecast_timesteps = filter_location_forecast(
        forecast,
        time_series,
        keys=[
            ["next_6_hours", "summary", "symbol_code"],
            ["instant", "details", "air_temperature"],
            ["next_6_hours", "details", "precipitation_amount"],
            ["instant", "details", "wind_speed"],
            ["instant", "details", "cloud_area_fraction"],
        ],
    )

    location_text = Text()
    location_text.append("📍 ", style="bold green")
    location_text.append(selected_location["name"], style="bold")
    content = Group(location_text, "")
    current_day = time_series[0].date()
    location_text = Text()
    location_text.append("📍 ", style="bold green")
    location_text.append(selected_location["name"], style="bold")
    content = Group(location_text, "")
    weather_table = create_weather_table(current_day)
    for forecast_timestep_time, filtered_data in filtered_forecast_timesteps.items():
        if forecast_timestep_time.date() != current_day:
            current_day = forecast_timestep_time.date()
            if weather_table.rows:
                content.renderables.append(weather_table)
                weather_table = create_weather_table(current_day)
        summary = filtered_data["symbol_code"].replace("_", " ").title()
        temp = f"{filtered_data['air_temperature']:.1f}°C"
        precipitation_amount = filtered_data["precipitation_amount"]
        rain = "" if float(precipitation_amount) == 0 else f"{precipitation_amount} mm"
        wind = f"{filtered_data['wind_speed']:.1f} m/s"
        cloud = f"{filtered_data['cloud_area_fraction']:.0f}%"
        time_str = f"{_get_24_hr_fmt(forecast_timestep_time.hour)}"
        weather_table.add_row(time_str, summary, temp, rain, wind, cloud)
    if weather_table.rows:
        content.renderables.append(weather_table)

    weather_panel = Panel(
        content,
        title="[bold blue]Weekend Weather Forecast[/bold blue]",
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
