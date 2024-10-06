"""https://api.met.no/weatherapi/locationforecast/2.0/swagger"""

from typing import List, Literal, Optional, TypedDict


class PointGeometry(TypedDict):
    type: Literal["Point"]
    coordinates: List[float]


WeatherSymbol = Literal[
    "clearsky_day",
    "clearsky_night",
    "clearsky_polartwilight",
    "fair_day",
    "fair_night",
    "fair_polartwilight",
    "lightssnowshowersandthunder_day",
    "lightssnowshowersandthunder_night",
    "lightssnowshowersandthunder_polartwilight",
    "lightsnowshowers_day",
    "lightsnowshowers_night",
    "lightsnowshowers_polartwilight",
    "heavyrainandthunder",
    "heavysnowandthunder",
    "rainandthunder",
    "heavysleetshowersandthunder_day",
    "heavysleetshowersandthunder_night",
    "heavysleetshowersandthunder_polartwilight",
    "heavysnow",
    "heavyrainshowers_day",
    "heavyrainshowers_night",
    "heavyrainshowers_polartwilight",
    "lightsleet",
    "heavyrain",
    "lightrainshowers_day",
    "lightrainshowers_night",
    "lightrainshowers_polartwilight",
    "heavysleetshowers_day",
    "heavysleetshowers_night",
    "heavysleetshowers_polartwilight",
    "lightsleetshowers_day",
    "lightsleetshowers_night",
    "lightsleetshowers_polartwilight",
    "snow",
    "heavyrainshowersandthunder_day",
    "heavyrainshowersandthunder_night",
    "heavyrainshowersandthunder_polartwilight",
    "snowshowers_day",
    "snowshowers_night",
    "snowshowers_polartwilight",
    "fog",
    "snowshowersandthunder_day",
    "snowshowersandthunder_night",
    "snowshowersandthunder_polartwilight",
    "lightsnowandthunder",
    "heavysleetandthunder",
    "lightrain",
    "rainshowersandthunder_day",
    "rainshowersandthunder_night",
    "rainshowersandthunder_polartwilight",
    "rain",
    "lightsnow",
    "lightrainshowersandthunder_day",
    "lightrainshowersandthunder_night",
    "lightrainshowersandthunder_polartwilight",
    "heavysleet",
    "sleetandthunder",
    "lightrainandthunder",
    "sleet",
    "lightssleetshowersandthunder_day",
    "lightssleetshowersandthunder_night",
    "lightssleetshowersandthunder_polartwilight",
    "lightsleetandthunder",
    "partlycloudy_day",
    "partlycloudy_night",
    "partlycloudy_polartwilight",
    "sleetshowersandthunder_day",
    "sleetshowersandthunder_night",
    "sleetshowersandthunder_polartwilight",
    "rainshowers_day",
    "rainshowers_night",
    "rainshowers_polartwilight",
    "snowandthunder",
    "sleetshowers_day",
    "sleetshowers_night",
    "sleetshowers_polartwilight",
    "cloudy",
    "heavysnowshowersandthunder_day",
    "heavysnowshowersandthunder_night",
    "heavysnowshowersandthunder_polartwilight",
    "heavysnowshowers_day",
    "heavysnowshowers_night",
    "heavysnowshowers_polartwilight",
]


class ForecastUnits(TypedDict, total=False):
    air_pressure_at_sea_level: str
    air_temperature: str
    air_temperature_max: str
    air_temperature_min: str
    cloud_area_fraction: str
    cloud_area_fraction_high: str
    cloud_area_fraction_low: str
    cloud_area_fraction_medium: str
    dew_point_temperature: str
    fog_area_fraction: str
    precipitation_amount: str
    precipitation_amount_max: str
    precipitation_amount_min: str
    probability_of_precipitation: str
    probability_of_thunder: str
    relative_humidity: str
    ultraviolet_index_clear_sky_max: str
    wind_from_direction: str
    wind_speed: str
    wind_speed_of_gust: str


class ForecastTimeInstant(TypedDict, total=False):
    air_pressure_at_sea_level: float
    air_temperature: float
    cloud_area_fraction: float
    cloud_area_fraction_high: float
    cloud_area_fraction_low: float
    cloud_area_fraction_medium: float
    dew_point_temperature: float
    fog_area_fraction: float
    relative_humidity: float
    wind_from_direction: float
    wind_speed: float
    wind_speed_of_gust: float


class ForecastTimePeriod(TypedDict, total=False):
    air_temperature_max: float
    air_temperature_min: float
    precipitation_amount: float
    precipitation_amount_max: float
    precipitation_amount_min: float
    probability_of_precipitation: float
    probability_of_thunder: float
    ultraviolet_index_clear_sky_max: float


class ForecastSummary(TypedDict):
    symbol_code: WeatherSymbol


class ForecastTimeStepInstant(TypedDict):
    instant: ForecastTimeInstant


class ForecastTimeStepNext12Hours(TypedDict):
    summary: ForecastSummary
    details: ForecastTimePeriod


class ForecastTimeStepNext1Hours(TypedDict):
    summary: ForecastSummary
    details: ForecastTimePeriod


class ForecastTimeStepNext6Hours(TypedDict):
    summary: ForecastSummary
    details: ForecastTimePeriod


class ForecastTimeStepData(TypedDict):
    instant: ForecastTimeInstant
    next_12_hours: Optional[ForecastTimeStepNext12Hours]
    next_1_hours: Optional[ForecastTimeStepNext1Hours]
    next_6_hours: Optional[ForecastTimeStepNext6Hours]


class ForecastTimeStep(TypedDict):
    time: str
    data: ForecastTimeStepData


class ForecastMeta(TypedDict):
    updated_at: set
    units: ForecastUnits


class Forecast(TypedDict):
    meta: ForecastMeta
    timeseries: List[ForecastTimeStep]


class METJSONForecast(TypedDict):
    type: Literal["Feature"]
    geometry: PointGeometry
    properties: Forecast
