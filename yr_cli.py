from typing import List, Optional
from urllib.parse import quote_plus

import inquirer
import requests
import typer
import yr_weather
from rich.console import Console
from rich.panel import Panel

app = typer.Typer()
console = Console()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT_HEADER = {"User-Agent": "YrCLI/0.1 github.com/yr-cli"}


def get_locations(query: str, limit: int = 10, country_code: str = "za") -> List[dict]:
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


@app.command()
def weather(
    location: Optional[str] = typer.Argument(None),
    limit: int = typer.Option(10, help="Maximum number of location results"),
    country_code: str = typer.Option("za", help="Country code for location search"),
):
    if location is None:
        location = prompt_location()

    locations = get_locations(location, limit, country_code)

    if not locations:
        console.print("[bold red]Error:[/bold red] No locations found.")
        return

    if len(locations) > 1:
        selected_location = select_location(locations)
    else:
        selected_location = locations[0]

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

    weather_info = f"""
    [bold]Location:[/bold] {selected_location['display_name']}
    [bold]Temperature:[/bold] {temp}°C
    [bold]Summary:[/bold] {summary}
    [bold]Rain:[/bold] {rain} mm
    [bold]Wind speed:[/bold] {wind_speed} m/s
    [bold]Cloud area fraction:[/bold] {cloud_area_fraction}%
    """

    console.print(Panel(weather_info, title="Weather Information", expand=False))


if __name__ == "__main__":
    app()
