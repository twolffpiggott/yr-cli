import base64
import io
import sys
from datetime import date, datetime
from functools import wraps
from typing import Callable, Dict, List, Optional

import inquirer
from PIL import Image
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.traceback import install

from . import get_icon_path
from .api import get_openstreetmap_locations
from .cache import cache_location, clear_cache, get_cached_location
from .maps import create_map_with_box
from .utils import get_output_method

OSC = b"\033]"
ST = b"\007"


class AnsiStyles:
    RESET = b"\033[0m"
    BOLD = b"\033[1m"
    RED = b"\033[31m"
    LIGHT_BLUE = b"\033[94m"
    YELLOW = b"\033[33m"
    DEFAULT = b""


console = Console()


def encode_image(image_path: str, max_width: int = 2, max_height: int = 1) -> bytes:
    with Image.open(image_path) as img:
        img.thumbnail((max_width * 10, max_height * 20))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        return b"".join(
            [
                OSC,
                b"1337;File=inline=1;width=",
                str(max_width).encode(),
                b";height=",
                str(max_height).encode(),
                b":",
                img_str,
                ST,
            ]
        )


def format_table_row(
    columns: list, image_column: Optional[int] = None, image_path: Optional[str] = None
) -> bytes:
    row = []
    for i, (col, width, color) in enumerate(columns):
        if i == image_column and image_path:
            icon = encode_image(image_path)
            # assume icon takes 2 characters
            padding = b" " * (width - 2)
            row.append(icon + padding)
        else:
            colored_text = (
                color
                + f"{col:<{width}}".encode()
                + (AnsiStyles.RESET if color != AnsiStyles.DEFAULT else b"")
            )
            row.append(colored_text)
    return b"".join(row).rstrip() + b"\n"


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


def get_wind_direction_arrow(degrees: float) -> str:
    """
    Convert wind direction in degrees to a corresponding arrow symbol.

    >>> [get_wind_direction_arrow(d) for d in range(0, 361, 45)]
    ['↓', '↙', '←', '↖', '↑', '↗', '→', '↘', '↓']
    >>> get_wind_direction_arrow(359)
    '↓'
    >>> get_wind_direction_arrow(360)
    '↓'
    >>> get_wind_direction_arrow(361)
    '↓'
    """
    directions = [
        ("N", "↓"),
        ("NE", "↙"),
        ("E", "←"),
        ("SE", "↖"),
        ("S", "↑"),
        ("SW", "↗"),
        ("W", "→"),
        ("NW", "↘"),
    ]

    degrees_per_direction = 360 / len(directions)
    index = int(
        (degrees % 360 + degrees_per_direction / 2) % 360 / degrees_per_direction
    )

    return directions[index][1]


def print_weather_table(forecast_timesteps: Dict[datetime, dict]):
    columns = [
        ("Time", 10, AnsiStyles.DEFAULT),
        ("", 10, AnsiStyles.DEFAULT),
        ("Temp (°C)", 10, AnsiStyles.RED),
        ("Rain (mm)", 10, AnsiStyles.LIGHT_BLUE),
        ("Wind (m/s)", 10, AnsiStyles.DEFAULT),
        ("Cloud (%)", 10, AnsiStyles.YELLOW),
    ]

    output = []
    current_day = min(forecast_timesteps).date()
    output.append(
        AnsiStyles.BOLD
        + f"{current_day.strftime('%A %d. %B')}\n".encode()
        + AnsiStyles.RESET
    )

    for timestamp, data in forecast_timesteps.items():
        if timestamp.date() != current_day:
            current_day = timestamp.date()
            output.append(
                AnsiStyles.BOLD
                + f"{current_day.strftime('%A %d. %B')}\n".encode()
                + AnsiStyles.RESET
            )

        formatted_row = [
            (timestamp.strftime("%H:%M"), columns[0][1], columns[0][2]),
            ("", columns[1][1], columns[1][2]),
            (f"{data['air_temperature']:.1f}°", columns[2][1], columns[2][2]),
            (f"{data['precipitation_amount']:.1f}", columns[3][1], columns[3][2]),
            (
                f"{data['wind_speed']:.1f}{get_wind_direction_arrow(data['wind_from_direction'])}",
                columns[4][1],
                columns[4][2],
            ),
            (f"{data['cloud_area_fraction']:.0f}%", columns[5][1], columns[5][2]),
        ]
        output.append(
            format_table_row(
                formatted_row,
                image_column=1,
                image_path=get_icon_path(data["symbol_code"]),
            )
        )

    full_output = b"".join(output)

    # use buffering to display output as a single block
    sys.stdout.buffer.write(b"\033[?2026h")
    sys.stdout.buffer.flush()
    sys.stdout.buffer.write(full_output)
    sys.stdout.buffer.flush()
    sys.stdout.buffer.write(b"\033[?2026l")
    sys.stdout.buffer.flush()


def get_selected_location(
    location: Optional[str],
    limit: int,
    country_code: str,
    no_cache: bool,
    show_map: bool,
) -> Optional[dict]:
    if location is None:
        location = prompt_location()
    if no_cache:
        selected_location = get_location(
            query=location, limit=limit, country_code=country_code, show_map=show_map
        )
    else:
        cached_location = get_cached_location(location)
        if cached_location:
            selected_location = cached_location
            if show_map and get_output_method() == "iterm2":
                create_map_with_box(
                    float(selected_location["lat"]), float(selected_location["lon"])
                )
        else:
            selected_location = get_location(
                query=location,
                limit=limit,
                country_code=country_code,
                show_map=show_map,
            )
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


def get_location(
    query: str, limit: int, country_code: str, show_map: bool
) -> Optional[dict]:
    locations = get_openstreetmap_locations(query, limit, country_code)
    if not locations:
        console.print("[bold red]Error:[/bold red] No locations found.")
        return None
    if len(locations) > 1:
        selected_location = select_location(locations)
        # always show map if there are multiple locations
        if get_output_method() == "iterm2":
            create_map_with_box(
                float(selected_location["lat"]), float(selected_location["lon"])
            )
    else:
        selected_location = locations[0]
        if show_map and get_output_method() == "iterm2":
            create_map_with_box(
                float(selected_location["lat"]), float(selected_location["lon"])
            )
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
