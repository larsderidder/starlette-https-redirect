# starlette-https-redirect

HTTPS redirect middleware for Starlette and FastAPI with configurable path exceptions.

## Install

Install from source:

```bash
git clone https://github.com/larsderidder/starlette-https-redirect.git
cd starlette-https-redirect
python -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install .
```

## Usage

```python
from starlette.applications import Starlette
from starlette_https_redirect import HTTPSRedirectMiddleware

app = Starlette()
app.add_middleware(HTTPSRedirectMiddleware, excepted_paths=["/health"])
```

With FastAPI:

```python
from fastapi import FastAPI
from starlette_https_redirect import HTTPSRedirectMiddleware

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware, excepted_paths=["/health"])
```

All HTTP requests are redirected to HTTPS with a 307 Temporary Redirect, except
for paths listed in `excepted_paths`, which are passed through unchanged. This
is useful for health-check endpoints called over plain HTTP by load balancers.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
pytest
```
