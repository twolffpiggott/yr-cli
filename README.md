# Yr Weather CLI

[yr.no](https://www.yr.no/nb) has a great weather service but poor search functionality, especially for South African place names. `yr` is a simple CLI that combines [OpenStreetMaps search engine](https://nominatim.openstreetmap.org/ui/search.html) with [yr's location forecast](https://api.met.no/weatherapi/locationforecast/2.0/documentation) to provide precise weather forecasts from place names in the command line.

<p align="center">
  <img src="https://github.com/twolffpiggott/yr-cli/raw/main/imgs/intro.gif" width="600">
</p>

# Usage

> You can use the `--help` option to get more details about the commands and their options

```bash
yr <command> [options]
```

## Now

> Detailed forecast for the next 24 hours

```bash
yr now <location>
```

Options

```
--limit                 INTEGER  Maximum number of location results [default: 10]
--country-code          TEXT     Country code for location search [default: za]
--no-cache                       Bypass cache and fetch fresh data
--map           -m               Show a map of the selected location
```

Examples

```
yr now silvermine                            Give a detailed forecast for Silvermine, South Africa
yr now silvermine -m --country-code ca       Give a detailed forecast for Silvermine, Canada, showing a map
```

## Summary

> Summary forecast for the next <days> (default 5) days

```bash
yr summary <location>
```

Options

```
--days                  INTEGER  Number of days for summary forecast [default: 5]
--limit                 INTEGER  Maximum number of location results [default: 10]
--country-code          TEXT     Country code for location search [default: za]
--no-cache                       Bypass cache and fetch fresh data
--map           -m               Show a map of the selected location
```

Examples

```
yr summary 'de pakhuys' --limit 5      Give a summary forecast for De Pakhuys, South Africa with at most 5 results
yr summary 'de pakhuys' --days 7       Give a summary forecast for De Pakhuys, South Africa for the next 7 days
```

## Weekend

> Forecast for the next weekend

```bash
yr weekend <location>
```

Options

```
--limit                 INTEGER  Maximum number of location results [default: 10]
--country-code          TEXT     Country code for location search [default: za]
--no-cache                       Bypass cache and fetch fresh data
--map           -m               Show a map of the selected location
```

Examples

```
yr weekend 'sassies bouldering'       Give a weekend forecast for Sassies Bouldering, Rocklands, South Africa
```

pip install -e .

# get a 24 hr forecast
yr now silvermine

# try it for another country
yr now silvermine --country-code ca --no-cache
```

## Development

To install `yr_cli` for development, run:

```bash
pip install -e '.[dev]'
```

Code for this repository is checked using [pre-commit](https://pre-commit.com/). After cloning this repository please run the following steps to initialise pre-commit:

```bash
pre-commit install --install-hooks
```

The following hooks are automatically run when new commits are made:

- From [pre-commit hooks](https://github.com/pre-commit/pre-commit-hooks):
    - end-of-file-fixer
    - trailing-whitespace
    - check-yaml
    - check-added-large-files (max. 500kb)
- [black](https://github.com/psf/black) Python code format checking
- [flake8](https://gitlab.com/pycqa/flake8) Python code linting
- [isort](https://github.com/PyCQA/isort) Python code import ordering
