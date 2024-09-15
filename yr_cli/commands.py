from datetime import datetime, timedelta, timezone
from typing import Optional

from .interface import display_weather, get_selected_location, handle_command_errors
from .locationforecast.data import fetch_and_filter_forecast


@handle_command_errors
def now_command(location: Optional[str], limit: int, country_code: str, no_cache: bool):
    selected_location = get_selected_location(location, limit, country_code, no_cache)
    if not selected_location:
        return

    now_dt = datetime.now().astimezone()
    start_time = now_dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    time_series = [start_time + timedelta(hours=hours) for hours in range(25)]

    filtered_forecast_timesteps = fetch_and_filter_forecast(
        selected_location, time_series
    )

    display_weather(
        filtered_forecast_timesteps,
        selected_location,
        "24-Hour Weather Forecast",
    )


@handle_command_errors
def summary_command(
    location: Optional[str], days: int, limit: int, country_code: str, no_cache: bool
):
    selected_location = get_selected_location(location, limit, country_code, no_cache)
    if not selected_location:
        return

    # yr only gives medium-term summary forecasts at defined 6-hour increments of UTC time
    now_dt = datetime.now().astimezone()
    utc_now = now_dt.astimezone(timezone.utc)
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

    filtered_forecast_timesteps = fetch_and_filter_forecast(
        selected_location, time_series
    )

    display_weather(
        filtered_forecast_timesteps,
        selected_location,
        "Summary Weather Forecast",
    )


@handle_command_errors
def weekend_command(
    location: Optional[str], limit: int, country_code: str, no_cache: bool
):
    selected_location = get_selected_location(location, limit, country_code, no_cache)
    if not selected_location:
        return

    now_dt = datetime.now().astimezone()
    utc_now = now_dt.astimezone(timezone.utc)
    days_to_friday = 4 - now_dt.weekday()
    if days_to_friday <= 0:
        days_to_friday += 7
    start_time = (
        now_dt.replace(minute=0, second=0, microsecond=0)
        + timedelta(hours=1)
        + timedelta(days=days_to_friday)
    )
    utc_start_time = (
        utc_now.replace(minute=0, second=0, microsecond=0)
        + timedelta(hours=1)
        + timedelta(days=days_to_friday)
    )
    time_series = []
    # yr only gives medium-term summary forecasts at defined 6-hour increments of UTC time
    # if more granular data is available (within the next two days), use it
    utc_summary_hours = [0, 6, 12, 18]
    # fri, sat, sun
    for day in range(3):
        if days_to_friday <= 2:
            granular_local_hours = range(24)
            if days_to_friday == 0:
                granular_local_hours = range(start_time.hour, 24)
            hours_for_day = [
                start_time.replace(hour=hour, minute=0, second=0, microsecond=0)
                + timedelta(days=day)
                for hour in granular_local_hours
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

    filtered_forecast_timesteps = fetch_and_filter_forecast(
        selected_location, time_series
    )

    display_weather(
        filtered_forecast_timesteps,
        selected_location,
        "Weekend Weather Forecast",
    )
