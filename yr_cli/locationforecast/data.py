from datetime import datetime, timedelta, timezone
from typing import Dict, List

from ..api import get_location_forecast
from .type import ForecastTimeStep, METJSONForecast


def fetch_and_filter_forecast(
    selected_location: dict, time_series: List[datetime]
) -> Dict[datetime, dict]:
    forecast: METJSONForecast = get_location_forecast(
        lat=float(selected_location["lat"]), lon=float(selected_location["lon"])
    )
    filtered_forecast_timesteps = filter_location_forecast(
        forecast,
        time_series,
        keys=[
            ["next_6_hours", "summary", "symbol_code"],
            ["instant", "details", "air_temperature"],
            ["next_6_hours", "details", "precipitation_amount"],
            ["instant", "details", "wind_speed"],
            ["instant", "details", "wind_from_direction"],
            ["instant", "details", "cloud_area_fraction"],
        ],
    )
    return filtered_forecast_timesteps


def filter_location_forecast(
    location_forecast: METJSONForecast,
    times: List[datetime],
    keys: Dict[str, str | Dict[str, dict]],
):
    filter_start_index = 0
    timeseries: List[ForecastTimeStep] = location_forecast["properties"]["timeseries"]
    filtered_results: Dict[str, Dict[str, str]] = dict()
    for time in times:
        for filter_index in range(filter_start_index, len(timeseries)):
            forecast_timestep = timeseries[filter_index]
            forecast_timestep_time = forecast_timestep["time"]
            utc_timestamp = _to_utc_timestamp(_to_nearest_hour(time))
            if utc_timestamp == forecast_timestep_time:
                forecast_timestep_data = forecast_timestep["data"]
                # assume times are sequential and economise
                filter_start_index = filter_index + 1
                break
            if utc_timestamp < forecast_timestep_time:
                raise ValueError(f"Time {utc_timestamp} not found")
        values = nested_lookup(forecast_timestep_data, keys)
        filtered_results[time] = values
    return filtered_results


def get_nested_value(data: dict, keys: List[str]) -> dict | str:
    """
    >>> data = {"a": {"b": {"c": "d"}}, "e": "f"}
    >>> get_nested_value(data, ["a", "b", "c"])
    'd'
    >>> get_nested_value(data, ["a", "b"])
    {'c': 'd'}
    >>> get_nested_value(data, ["e"])
    'f'
    """
    return get_nested_value(data[keys[0]], keys[1:]) if keys else data


def nested_lookup(data: dict, lookup: List[str | List[str]]) -> dict:
    """
    >>> data = {"a": 1, "b": {"c": 2, "d": 3}}
    >>> lookup = ["a", ["b", "c"]]
    >>> nested_lookup(data, lookup)
    {'a': 1, 'c': 2}
    """
    # convert from more user-friendly format
    lookup_lists = [
        key_lookup if isinstance(key_lookup, list) else [key_lookup]
        for key_lookup in lookup
    ]
    return {
        lookup_list[-1]: get_nested_value(data, lookup_list)
        for lookup_list in lookup_lists
    }


def _to_utc_timestamp(time: datetime) -> str:
    """
    >>> _to_utc_timestamp(datetime(2023, 5, 15, 14, 30, 0, tzinfo=timezone.utc))
    '2023-05-15T14:30:00Z'
    >>> _to_utc_timestamp(datetime(2023, 5, 15, 14, 30, 0, tzinfo=timezone(timedelta(hours=2))))
    '2023-05-15T12:30:00Z'
    >>> _to_utc_timestamp(datetime(2023, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
    '2023-12-31T23:59:59Z'
    >>> _to_utc_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc))
    '2024-01-01T00:00:00Z'
    """
    return time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_nearest_hour(date: datetime) -> datetime:
    """
    >>> _to_nearest_hour(datetime(2023, 5, 15, 14, 29, 59, tzinfo=timezone.utc))
    datetime.datetime(2023, 5, 15, 14, 0, tzinfo=datetime.timezone.utc)
    >>> _to_nearest_hour(datetime(2023, 5, 15, 14, 30, 0, tzinfo=timezone.utc))
    datetime.datetime(2023, 5, 15, 15, 0, tzinfo=datetime.timezone.utc)
    >>> _to_nearest_hour(datetime(2023, 5, 15, 14, 45, 1, tzinfo=timezone.utc))
    datetime.datetime(2023, 5, 15, 15, 0, tzinfo=datetime.timezone.utc)
    >>> _to_nearest_hour(datetime(2023, 5, 15, 23, 59, 59, tzinfo=timezone.utc))
    datetime.datetime(2023, 5, 16, 0, 0, tzinfo=datetime.timezone.utc)
    """
    return date.replace(microsecond=0, second=0, minute=0) + timedelta(
        hours=date.minute // 30
    )
