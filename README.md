# Yr Weather CLI

[yr.no](https://www.yr.no/nb) has a great weather service, but poor search functionality, especially for South African place names. I built a simple CLI that combines [OpenStreetMaps search engine](https://nominatim.openstreetmap.org/ui/search.html) with [yr's location forecast](https://api.met.no/weatherapi/locationforecast/2.0/documentation).

```bash
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
