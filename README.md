# Yr Weather CLI

[yr.no](https://www.yr.no/nb) has a great weather service, but poor search functionality, especially for South African place names. I built a simple CLI that combines [OpenStreetMaps search engine](https://nominatim.openstreetmap.org/ui/search.html) with [yr's location forecast](https://api.met.no/weatherapi/locationforecast/2.0/documentation).

```bash
pip install -e .

# get a 24 hr forecast
yr now silvermine

# try it for another country
yr now silvermine --country-code ca --no-cache
```
