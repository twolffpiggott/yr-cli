from datetime import timedelta
from pathlib import Path
from typing import List
from urllib.parse import quote_plus

import requests
from requests_cache import CachedSession

from .locationforecast.type import METJSONForecast

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
MET_FORECAST_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
USER_AGENT_HEADER = {"User-Agent": "YrCLI/0.1 github.com/yr-cli"}
MET_CACHE_PATH = (Path.home() / ".met_cache.sqlite").as_posix()


def get_openstreetmap_locations(
    query: str, limit: int, country_code: str
) -> List[dict]:
    params = {
        "q": quote_plus(query),
        "format": "json",
        "limit": limit,
        "countrycodes": country_code,
    }
    response = requests.get(NOMINATIM_URL, params=params, headers=USER_AGENT_HEADER)
    response.raise_for_status()
    return response.json()


def get_location_forecast(lat: float, lon: float) -> METJSONForecast:
    session = CachedSession(
        MET_CACHE_PATH,
        cache_control=True,
        expire_after=timedelta(days=1),
    )
    params = {"lat": lat, "lon": lon}
    response = session.get(MET_FORECAST_URL, params=params, headers=USER_AGENT_HEADER)
    response.raise_for_status()
    location_forecast: METJSONForecast = response.json()
    return location_forecast
